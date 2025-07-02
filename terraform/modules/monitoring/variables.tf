variable "environment" {
  description = "Environment name (e.g., qa, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "rds_instances" {
  description = "List of RDS instance IDs to monitor"
  type        = list(string)
}

variable "ecs_services" {
  description = "List of ECS service names to monitor"
  type        = list(string)
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "alarm_email" {
  description = "Email address for CloudWatch alarms"
  type        = string
}
