variable "environment" {
  description = "Environment name (e.g., qa, prod)"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "ecs_security_group_ids" {
  description = "List of ECS service security group IDs"
  type        = list(string)
}

variable "management_security_group_ids" {
  description = "List of management instance security group IDs"
  type        = list(string)
  default     = []
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "route_table_ids" {
  description = "List of route table IDs for Gateway endpoints"
  type        = list(string)
}

variable "github_repo" {
  description = "GitHub repository path (e.g., organization/repo)"
  type        = string
}

variable "terraform_state_bucket" {
  description = "S3 bucket name for Terraform state"
  type        = string
}

variable "terraform_lock_table" {
  description = "DynamoDB table name for Terraform state locking"
  type        = string
}
