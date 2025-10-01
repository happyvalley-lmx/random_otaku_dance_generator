import numpy as np
import librosa
import scipy
from sklearn.cluster import KMeans

def extract_chorus_intervals(path, k=5, min_segment_duration=10.0, bpm_aggregate='median'):
    """Extract probable chorus interval(s) from an audio file.

    Implements the approach described in the article: CQT -> beat-sync -> recurrence matrix
    -> combine with path adjacency (MFCC) -> spectral clustering via Laplacian/evecs -> kmeans

    Returns: list of (start_time, end_time) in seconds for candidate chorus segments (sorted).
    """
    y, sr = librosa.load(path, sr=None)

    # 1. CQT and convert to dB
    BINS_PER_OCTAVE = 12
    N_OCTAVES = 7
    C = librosa.amplitude_to_db(np.abs(librosa.cqt(y=y, sr=sr,
                                                 bins_per_octave=BINS_PER_OCTAVE,
                                                 n_bins=N_OCTAVES * BINS_PER_OCTAVE)),
                                ref=np.max)

    # 2. Beat track and sync CQT
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, trim=False)
    if len(beats) == 0:
        # fallback to frame-based beats
        beats = np.arange(0, C.shape[1])
    Csync = librosa.util.sync(C, beats, aggregate=np.median)

    # 3. Recurrence matrix
    R = librosa.segment.recurrence_matrix(Csync, width=3, mode='affinity', sym=True)

    # 4. Strengthen diagonal smoothing: timelag_filter takes a filter function (e.g. scipy.ndimage.median_filter)
    df = librosa.segment.timelag_filter(scipy.ndimage.median_filter)
    Rf = df(R, size=(1, 7))

    # 5. MFCC path adjacency
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    Msync = librosa.util.sync(mfcc, beats)
    path_distance = np.sum(np.diff(Msync, axis=1)**2, axis=0)
    sigma = np.median(path_distance) if path_distance.size else 1.0
    path_sim = np.exp(-path_distance / (sigma + 1e-8))
    R_path = np.diag(path_sim, k=1) + np.diag(path_sim, k=-1)

    # 6. Combine adjacency matrices
    deg_path = np.sum(R_path, axis=1)
    deg_rec = np.sum(Rf, axis=1)
    mu = float(deg_path.dot(deg_path + deg_rec)) / (np.sum((deg_path + deg_rec)**2) + 1e-8)
    A = mu * Rf + (1 - mu) * R_path

    # 7. Laplacian and eigenvectors
    L = scipy.sparse.csgraph.laplacian(A, normed=True)
    evals, evecs = scipy.linalg.eigh(L)
    evecs = scipy.ndimage.median_filter(evecs, size=(9, 1))
    Cnorm = np.cumsum(evecs**2, axis=1)**0.5

    # 8. k-means on first k eigenvectors
    kc = min(k, evecs.shape[1])
    X = evecs[:, :kc] / (Cnorm[:, kc-1:kc] + 1e-8)
    KM = KMeans(n_clusters=kc, random_state=0)
    seg_ids = KM.fit_predict(X)

    # 9. Convert segment ids to time intervals
    # each column in Csync corresponds to a beat interval; map beat indices to times
    bound_beats = np.flatnonzero(np.concatenate(([True], seg_ids[1:] != seg_ids[:-1], [True])))
    # compute beat times
    beat_times = librosa.frames_to_time(beats, sr=sr)
    # ensure last boundary
    if bound_beats[-1] != len(seg_ids):
        bound_beats = np.append(bound_beats, len(seg_ids))

    intervals = []
    for i in range(len(bound_beats)-1):
        b0 = bound_beats[i]
        b1 = bound_beats[i+1]
        # map to time in seconds using beat index range
        t0 = beat_times[b0] if b0 < len(beat_times) else 0.0
        t1 = beat_times[b1] if b1 < len(beat_times) else librosa.get_duration(y=y, sr=sr)
        intervals.append((t0, t1, seg_ids[b0]))

    # 10. Filter short segments and compute energy per segment
    durations = [t1 - t0 for (t0, t1, _) in intervals]
    filtered = [(t0, t1, lbl) for (t0, t1, lbl), d in zip(intervals, durations) if d >= min_segment_duration]

    # energy by label
    meanCsync = np.mean(Csync, axis=0)
    label_time_map = {}
    label_energy = {}
    for t0, t1, lbl in filtered:
        # map times back to beat indices for energy aggregation
        # find beats within t0..t1
        bt_idx = np.where((beat_times >= t0) & (beat_times < t1))[0]
        if bt_idx.size == 0:
            energy = 0.0
        else:
            energy = np.mean(meanCsync[bt_idx])
        label_time_map.setdefault(lbl, []).append((t0, t1))
        label_energy[lbl] = label_energy.get(lbl, 0.0) + energy

    if not label_energy:
        return []

    # pick the label with highest energy
    target_label = max(label_energy.items(), key=lambda x: x[1])[0]
    # choose the last segment for that label (often chorus occurs later)
    seg_list = label_time_map.get(target_label, [])
    if not seg_list:
        return []
    chosen = seg_list[-1]

    return [chosen]
