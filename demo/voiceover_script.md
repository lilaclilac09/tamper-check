# tamper-check demo: voiceover script

Voice: Microsoft Edge neural TTS, `en-US-AndrewNeural` (via `edge-tts`). Times refer to the original `demo.mp4`. When narration runs longer than its segment, the segment's last frame is held (freeze frame) rather than cutting the narration.

| # | Video segment | On screen |
|---|---|---|
| 1 | 0:00–0:04 | Dashboard loads; 3D view of a Ledger Flex |
| 2 | 0:04–0:19.5 | Genuine scenario: LIKELY GENUINE, risk 0 |
| 3 | 0:19.5–0:35 | Glue on one side: SUSPICIOUS, red region in 3D, checklist |
| 4 | 0:35–0:50.5 | LTE implant: TAMPERED, cellular bursts, RF rings |
| 5 | 0:50.5–1:00 | Manual entry with 1 g kitchen scale: demo-only warning |
| 6 | 1:00–1:21 | Manual entry with 0.001 g scale: flagged, remediation checklist ticked |

## Narration

**1. Intro**
In October 2026, Ledger confirmed that hardware wallets sold through a reseller in Southeast Asia had an extra circuit board hidden inside. It reads the recovery phrase during setup and sends it out over a cellular link. Ledger's Genuine Check still passes, because the secure chip itself is untouched. This is tamper-check: software that looks for the physical change instead.

**2. Genuine**
The primary signal is weight. On a milligram scale, take at least three readings and re-zero between each one. They're averaged and compared with a reference unit from the same production batch. The reference weights in this demo are example values, not official specs. This unit is within tolerance, its center of mass hasn't moved, and it is silent on RF, so the verdict is likely genuine, risk zero.

**3. Glue on one side**
Now a blob of glue on one side. It adds a few hundred milligrams, which a precision scale easily catches. In the 3D view, green marks the expected center of mass, yellow the estimated one, and red the region where mass seems to have been added. Center of mass is an optional check, measured by tilting the device over a pivot with a phone. The verdict is suspicious, and a remediation checklist appears.

**4. LTE implant**
Next, a simulated implant. The device is powered off inside a Faraday bag while a radio scanner listens. A Ledger has no cellular radio, so any burst in the cellular bands is critical. Here they repeat about every thirty seconds, shown as red rings. But silence isn't proof: an implant may only transmit after setup. Weight plus RF: tampered, do not use, risk one hundred.

**5. Kitchen scale**
What about a kitchen scale? With one-gram resolution, the same measurement looks fine, and the tool warns that this is demo-only. It cannot catch milligram-level implants.

**6. Diamond scale and checklist**
With a milligram scale, the extra three hundred milligrams are flagged right away. The verdict and risk score come from simple rules you can read. Then follow the checklist: do not enter a seed on this device. Run Genuine Check and confirm the firmware, but remember it can't see added boards. If funds were ever on a seed from this device, move them to a new wallet bought directly from Ledger, with a new seed. Report it, and only then open the device to inspect. Weigh before you trust.
