import os
import sys
import tempfile

import oci


def env(name):
    value = os.environ.get(name)
    if not value:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def set_output(key, value):
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as fh:
            fh.write(f"{key}={value}\n")


def main():
    private_key_content = env("OCI_PRIVATE_KEY")

    # The OCI SDK wants a path to a key file, so write the key (from the
    # GitHub secret) to a temp file that only this job can see.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
        f.write(private_key_content)
        if not private_key_content.endswith("\n"):
            f.write("\n")
        key_path = f.name
    os.chmod(key_path, 0o600)

    config = {
        "user": env("OCI_USER_OCID"),
        "key_file": key_path,
        "fingerprint": env("OCI_FINGERPRINT"),
        "tenancy": env("OCI_TENANCY_OCID"),
        "region": env("OCI_REGION"),
    }
    oci.config.validate_config(config)

    compute = oci.core.ComputeClient(config)

    details = oci.core.models.LaunchInstanceDetails(
        compartment_id=env("OCI_COMPARTMENT_OCID"),
        availability_domain=env("OCI_AVAILABILITY_DOMAIN"),
        shape="VM.Standard.A1.Flex",
        shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
            ocpus=2,
            memory_in_gbs=12,
        ),
        display_name="n8n-claude-vm",
        create_vnic_details=oci.core.models.CreateVnicDetails(
            subnet_id=env("OCI_SUBNET_OCID"),
            assign_public_ip=True,
        ),
        source_details=oci.core.models.InstanceSourceViaImageDetails(
            image_id=env("OCI_IMAGE_OCID"),
        ),
        metadata={
            "ssh_authorized_keys": env("OCI_SSH_PUBLIC_KEY"),
        },
    )

    try:
        response = compute.launch_instance(details)
        instance_id = response.data.id
        print(f"Success! Instance created: {instance_id}")
        set_output("created", "true")
        set_output("instance_id", instance_id)
    except oci.exceptions.ServiceError as e:
        message = str(e.message or "")
        if "Out of host capacity" in message or "LimitExceeded" in str(e.code) or e.status in (500, 429):
            print(f"No capacity yet ({e.code}): {message}")
            set_output("created", "false")
            sys.exit(0)
        print(f"Unexpected OCI error ({e.code}): {message}", file=sys.stderr)
        set_output("created", "false")
        sys.exit(1)


if __name__ == "__main__":
    main()
