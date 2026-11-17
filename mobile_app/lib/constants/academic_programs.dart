/// Centralized academic programme list for IIPS DAVV.
/// In IIPS DAVV, M.Tech is an integrated 5-year programme with IT and CS specializations.
const List<String> academicPrograms = [
  "MCA",
  "M.Tech (IT)",
  "M.Tech (CS)",
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
