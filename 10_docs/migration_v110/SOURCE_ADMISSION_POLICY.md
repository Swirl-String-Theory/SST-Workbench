# Standing source-admission rule

User instruction, 26 October 2026: "Bron altijd toelaten als het op lokaal of op Google drive staat".

For this SST-Workbench migration pipeline, local files and user-accessible Google Drive files are admitted as source choices under standing user authorization. Do not ask again merely because an independent publisher signature or a previously trusted external archive hash is unavailable. This rule supplies the explicit provenance consent requested by the earlier P02/P03 source-admission conditions.

Record the actual path or Drive file/revision identity, retrieved byte size, SHA-256, package version, manifest results and remaining provenance limits. Preserve the retrieved original bytes. A user-authorized source must not be described as independently publisher-authenticated unless that is separately demonstrated.

Existing integrity, exact-version, dataset-admission, capability and blind/reveal checks remain applicable. An integrity error still stops execution; never repair a historical manifest to match modified bytes. Preserve historical versions, results and commitments. Source admission does not change scientific qualifications, provider-independence requirements, execution budgets or campaign-release conditions.

Machine-readable policy: SOURCE_ADMISSION_POLICY.json. The persistent queue and the existing Scheduled task reference this rule. Their current execution scope and scheduling remain unchanged by this policy update.
