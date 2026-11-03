# Limits of authenticity assessment

The planned software provides visual observations for human review. It cannot certify that an identity card is genuine, prove identity, or establish document validity with an issuing authority.

- An ordinary RGB scan/photo cannot reliably verify tactile printing, substrate, hologram motion, UV/IR features, chip data or cryptographic signatures. Chip/NFC and authority verification are outside MVP.
- Blur, glare, compression, cropping, resampling, camera processing and lighting may hide evidence or create apparent anomalies. Insufficient quality must be reported as inconclusive.
- OCR can misread scripts, names, diacritics and dates. Confidence is not an authenticity probability; reviewers must be able to compare extracted text with the source.
- Correct field formats or MRZ check digits only demonstrate limited consistency. They do not prove authenticity. An inconsistent field may result from OCR error or damage.
- Templates vary by country, issue period and document version. Only explicitly documented profiles may be evaluated. An unknown version is unsupported, not proof of fraud.
- Any future detector will have false positives and false negatives. No accuracy, error-rate or coverage claims exist until measured on a lawful, representative, independently held-out dataset with reported uncertainty.
- Image-only analysis cannot establish who holds a document or whether it was lost, revoked or stolen. Examiner findings must state scope and uncertainty and remain separate from automated observations.

MVP output vocabulary: observations present, no observations detected within supported checks, insufficient quality, unsupported document, and processing error. No observations detected must never be presented as proof of authenticity.

Evaluation will separate OCR accuracy, quality rejection, profile coverage and anomaly detection performance. Synthetic fixtures are suitable for engineering tests but cannot establish real-world forensic accuracy.
