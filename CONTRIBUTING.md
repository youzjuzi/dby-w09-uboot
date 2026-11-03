# Contributing

Thank you for your interest. This project targets one device, so changes are reviewed with that in mind.

## Reporting problems

Open an issue and include:

- device model and stock firmware version;
- the U-Boot commit or version you built;
- what you expected and what happened (a photo of the screen is fine);
- how you built and flashed it.

**Remove personal data before posting:** Wi-Fi names, IP and MAC addresses, serial numbers and country codes.

## Proposing changes

Please open an issue to discuss a change before sending a pull request.

- Keep each patch small and limited to one purpose.
- Follow the modified file’s declared licence. New files carry an SPDX header for their component: U-Boot integration code uses `GPL-2.0-or-later`; host tools use `GPL-2.0-only`.
- Anything that writes to storage needs a clear justification and must not widen the existing write gates.
- State how a change was tested: on a real device, in a simulator, or only reviewed. Do not describe untested code as working.

## Licensing

Contributions follow the licence declared by the modified file, including file-specific exceptions. New U-Boot integration code uses GPL-2.0-or-later; new host tools use GPL-2.0-only. By submitting a change you confirm you have the right to do so.

## Out of scope

Distribution of Huawei firmware or other proprietary binaries is not accepted in this repository.
