export interface JobImageSource {
  postType?: string;
  origin?: string;
  destination?: string;
}

export const FALLBACK_JOB_IMAGE = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="500" height="300"><rect width="100%" height="100%" fill="%23f0f4f8"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%236779" font-size="20">No product image provided</text></svg>';

export const isCurrentUserId = (candidateId?: string | number | null, currentUserId?: string | number | null) => {
  return String(candidateId ?? '') === String(currentUserId ?? '');
};

export const resolveJobImage = (job: JobImageSource) => {
  return FALLBACK_JOB_IMAGE;
};
