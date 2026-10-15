# Oracle Free Tier VM Retry

This repo automatically keeps trying to create a **2 OCPU / 12 GB Ampere A1.Flex** "Always Free" virtual machine on Oracle Cloud in the `ap-hyderabad-1` region, since Oracle's free ARM capacity is often all used up and only opens up occasionally.

## How it works

A GitHub Actions workflow (`.github/workflows/retry.yml`) runs every 5 minutes. Each run:

1. Tries to create the VM using Oracle's API.
2. If Oracle replies "out of capacity", it just stops quietly — the next scheduled run tries again 5 minutes later.
3. If it succeeds, it opens a GitHub Issue in this repo telling you the VM was created, and turns off the schedule so it stops trying.

## Checking progress

- **Actions tab**: see every attempt and whether it found capacity.
- **Issues tab**: this is where you'll see the "Your Oracle VM is ready" notification once it succeeds.

## Setup (already done)

All the account details (tenancy, user, region, network, image, SSH key, etc.) are stored as encrypted repository secrets under **Settings > Secrets and variables > Actions**. Nothing sensitive lives in the code itself.

## Logging in once the VM is created

Once you get the "ready" issue, open the Oracle Cloud console → Compute → Instances to find the new VM's public IP address, then connect with:

```
ssh -i /path/to/your/private-key opc@<public-ip>
```

(or `ubuntu@<public-ip>` depending on the image), using the SSH private key you downloaded during setup.
