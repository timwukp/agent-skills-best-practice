---
name: terraform-module
description: >
  Creates Terraform modules following AWS Well-Architected Framework best practices.
  Generates variable definitions, outputs, documentation, and module composition patterns
  for common AWS services including VPC, ECS, Lambda, RDS, and S3.
  Triggers on: "create Terraform module", "infrastructure as code", "IaC", "provision AWS resources".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: infrastructure
---

# Terraform Module

## Instructions

### Step 1: Gather Requirements

Ask:
1. What AWS resources are needed? (VPC, ECS, Lambda, RDS, S3, CloudFront)
2. What environment? (dev, staging, production, or multi-environment)
3. What compliance requirements? (encryption at rest, VPC isolation, logging)
4. Existing infrastructure to integrate with? (VPC ID, subnets, security groups)
5. State backend? (S3+DynamoDB, Terraform Cloud, local)

### Step 2: Module Structure

Create the standard module layout:

```
modules/
  my-service/
    main.tf          # Primary resource definitions
    variables.tf     # Input variable declarations
    outputs.tf       # Output value declarations
    versions.tf      # Provider and terraform version constraints
    locals.tf        # Local values and computed expressions
    data.tf          # Data sources
    README.md        # Module documentation
```

**versions.tf (always include):**
```hcl
terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

### Step 3: Variable Definitions

Define variables with descriptions, types, and validation:

```hcl
variable "environment" {
  description = "Deployment environment (dev, staging, production)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "service_name" {
  description = "Name of the service, used for resource naming and tagging"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,28}$", var.service_name))
    error_message = "Service name must be lowercase, start with a letter, 3-29 chars."
  }
}

variable "vpc_config" {
  description = "VPC configuration for the service"
  type = object({
    vpc_id             = string
    private_subnet_ids = list(string)
    public_subnet_ids  = list(string)
  })
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
```

**Rules:**
- Always add `description` to every variable
- Use `validation` blocks for constrained inputs
- Use object types for related configuration groups
- Provide sensible defaults where possible
- Never default sensitive values (passwords, keys)

### Step 4: Resource Definitions

Apply Well-Architected Framework principles:

**Security:**
- Encrypt everything at rest (S3, RDS, EBS, SQS)
- Use least-privilege IAM policies
- Enable VPC flow logs
- Use security groups as allowlists

**Reliability:**
- Multi-AZ deployments for production
- Auto-scaling with appropriate thresholds
- Health checks on all services
- Backup and retention policies

**Cost Optimization:**
- Use `locals` for environment-based sizing
- Tag all resources for cost allocation
- Use reserved capacity variables for production

```hcl
locals {
  name_prefix = "${var.service_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Environment = var.environment
    Service     = var.service_name
    ManagedBy   = "terraform"
  })

  sizing = {
    dev        = { instance_class = "db.t3.micro", min_capacity = 1 }
    staging    = { instance_class = "db.t3.small", min_capacity = 1 }
    production = { instance_class = "db.r6g.large", min_capacity = 2 }
  }
}
```

### Step 5: Common Module Patterns

**VPC Module:**
```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-vpc" })
}

resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone = var.availability_zones[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-${count.index + 1}"
    Tier = "private"
  })
}
```

**ECS Fargate Service:**
```hcl
resource "aws_ecs_service" "main" {
  name            = local.name_prefix
  cluster         = var.ecs_cluster_id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = local.sizing[var.environment].min_capacity
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.vpc_config.private_subnet_ids
    security_groups  = [aws_security_group.service.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = var.service_name
    container_port   = var.container_port
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
}
```

**S3 Bucket with Security:**
```hcl
resource "aws_s3_bucket" "main" {
  bucket = "${local.name_prefix}-${var.bucket_purpose}"
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "main" {
  bucket                  = aws_s3_bucket.main.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

### Step 6: Outputs

Expose values needed by other modules:

```hcl
output "service_url" {
  description = "URL of the deployed service"
  value       = "https://${aws_lb.main.dns_name}"
}

output "security_group_id" {
  description = "Security group ID of the service, for use in ingress rules"
  value       = aws_security_group.service.id
}

output "iam_role_arn" {
  description = "IAM role ARN of the ECS task, for granting additional permissions"
  value       = aws_iam_role.task.arn
}
```

### Step 7: Module Composition

Show how to use the module:

```hcl
module "api_service" {
  source = "./modules/ecs-service"

  service_name = "api"
  environment  = var.environment
  vpc_config   = module.vpc.config

  container_image = "${var.ecr_registry}/api:${var.image_tag}"
  container_port  = 8080

  tags = var.tags
}
```

## Example

User says: "Create a Terraform module for a Lambda function with API Gateway"

Response:
- Module with variables (function_name, runtime, handler, memory, timeout)
- Lambda function with IAM role and CloudWatch log group
- API Gateway HTTP API with Lambda integration
- Outputs (function_arn, api_endpoint, log_group_name)
- Usage example showing module invocation

## Guidelines

- Always pin provider versions with `~>` constraints
- Tag every resource with environment, service, and managed-by
- Use `locals` for computed values and naming conventions
- Validate inputs with `validation` blocks
- Encrypt all data at rest by default
- Use `for_each` over `count` when resources have meaningful identifiers
- Never hardcode AWS account IDs or regions; use data sources
- Include a README.md with usage examples for every module
- Separate state per environment using workspaces or directory structure
