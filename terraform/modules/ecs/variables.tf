variable "service_name" {
  description = "Name of the service (e.g., tax-service, invoice-service)"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., qa, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for the ECS service"
  type        = list(string)
}

variable "docker_image" {
  description = "Docker image to deploy (e.g., account-id.dkr.ecr.region.amazonaws.com/image:tag)"
  type        = string
}

variable "container_port" {
  description = "Port exposed by the container"
  type        = number
  default     = 8000
}

variable "task_cpu" {
  description = "CPU units for the ECS task (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "task_memory" {
  description = "Memory for the ECS task in MiB"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Number of instances of the task to run"
  type        = number
  default     = 2
}

variable "assign_public_ip" {
  description = "Whether to assign a public IP to the Fargate tasks"
  type        = bool
  default     = false
}

variable "database_url" {
  description = "PostgreSQL connection string"
  type        = string
  sensitive   = true
}

variable "rabbitmq_url" {
  description = "RabbitMQ connection string"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Domain name for the service (e.g., example.com)"
  type        = string
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS"
  type        = string
}

variable "ssm_parameter_prefix" {
  description = "Prefix for SSM parameters"
  type        = string
  default     = "/billing"
}

variable "sns_topic_arn" {
  description = "ARN of the SNS topic for alarms"
  type        = string
  default     = ""
}
