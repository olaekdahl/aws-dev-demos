# Bootstrap (Terraform remote state)

This optional stack creates:
- An S3 bucket for Terraform remote state
- A DynamoDB table for state locking

Run:

```bash
terraform init
terraform apply
```

Then configure the backend for `../app` (example):

```hcl
terraform {
  backend "s3" {
    bucket         = "<OUTPUT tfstate_bucket_name>"
    key            = "code-quiz/app.tfstate"
    region         = "us-west-2"
    dynamodb_table = "<OUTPUT terraform_lock_table_name>"
    encrypt        = true
  }
}
```

> For a demo or sandbox, you can skip remote state and just use local state.
