variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "aws_role_arn" {
  description = "AWS IAM role ARN to assume for federated access"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "db_username" {
  description = "Username for the RDS PostgreSQL instances"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Password for the RDS PostgreSQL instances"
  type        = string
  sensitive   = true
}

variable "github_repo" {
  description = "GitHub repository path (e.g., organization/repo)"
  type        = string
  default     = "your-org/billing-microservices"
}

variable "terraform_state_bucket" {
  description = "S3 bucket name for Terraform state"
  type        = string
}

variable "terraform_lock_table" {
  description = "DynamoDB table name for Terraform state locking"
  type        = string
}

variable "tax_service_image" {
  description = "Docker image for tax service"
  type        = string
}

variable "discount_service_image" {
  description = "Docker image for discount service"
  type        = string
}

variable "invoice_service_image" {
  description = "Docker image for invoice service"
  type        = string
}

variable "payment_service_image" {
  description = "Docker image for payment service"
  type        = string
}

variable "rabbitmq_url" {
  description = "RabbitMQ connection URL"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Domain name for the services"
  type        = string
  default     = "billing.example.com"
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS"
  type        = string
}

variable "alarm_email" {
  description = "Email address for CloudWatch alarms"
  type        = string
}

variable "jwt_public_key" {
  description = "JWT public key for authentication"
  type        = string
  sensitive   = true
}
