/// Centralized academic programme list for IIPS DAVV.
/// Used in registration, upload forms, and eligibility filtering.
const List<String> academicPrograms = [
  "MCA",
  "M.Tech",
  "MBA (MS)",
  "MBA (TA)",
  "BCA",
  "B.Com (Hons)",
  "IT",
  "CSE",
];

/// Extended list with "ALL" first — used by Faculty/Admin when uploading documents.
const List<String> uploadPrograms = [
  "ALL",
  ...academicPrograms,
];
