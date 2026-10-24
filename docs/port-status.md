# Torchlight II bring-up gates

The project is complete only when every gate below has evidence from the
current build. A generated IPA alone is not proof that the game runs.

| Gate | Required evidence | Current state |
|---|---|---|
| Local archive identity | Base, update, and optional DLC title IDs match the local dump | Done on Windows |
| Resource packaging | Every part is <= 500,000,000 bytes; manifest and round-trip hashes verify | Done on Windows |
| Public tree hygiene | No game archives, extracted content, or keys are tracked | Done |
| nxnative survey | Mac log and survey for title `010090400D366000` | Pending self-hosted macOS |
| Provisional profile | Generated profile, module census, SDK and graphics detection | Pending self-hosted macOS |
| Mac boot | Host reaches the title screen with no fatal error | Pending |
| iOS packaging | IPA built from the same local resource set | Pending |
| iPhone validation | iPhone 17 Pro Max launches, renders, accepts input, saves, and plays a short route | Pending |
| Verified profile | Any fixes are committed as public code/profile data without game assets | Pending |

The first Mac run should use `survey_only`. If the survey reaches extraction
and shader classification, keep its generated files in the local resource
directory and attach only sanitized logs to public issue discussions.
