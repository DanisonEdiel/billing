provider "aws" {
  region = var.aws_region
  assume_role {
    role_arn = var.aws_role_arn
  }
}

terraform {
  required_version = ">= 1.0.0"
  
  backend "s3" {
    # Variables will be provided via -backend-config CLI options
  }
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# VPC and Networking
module "vpc" {
  source = "../modules/vpc"
  
  environment = "prod"
  vpc_cidr    = var.vpc_cidr
  azs         = var.availability_zones
}

# Security Groups and IAM
module "security" {
  source = "../modules/security"
  
  vpc_id                    = module.vpc.vpc_id
  environment              = "prod"
  aws_region               = var.aws_region
  aws_account_id           = var.aws_account_id
  ecs_security_group_ids   = []
  management_security_group_ids = []
  private_subnet_ids       = module.vpc.private_subnets
  route_table_ids          = module.vpc.private_route_table_ids
  github_repo              = var.github_repo
  terraform_state_bucket   = var.terraform_state_bucket
  terraform_lock_table     = var.terraform_lock_table
}

# RDS PostgreSQL Instances
module "tax_db" {
  source = "../modules/rds"
  
  identifier           = "billing-tax-prod"
  allocated_storage    = 50
  engine_version       = "16.1"
  instance_class       = "db.t3.medium"
  db_name              = "tax_service"
  username             = var.db_username
  password             = var.db_password
  vpc_security_group_ids = [module.security.rds_sg_id]
  db_subnet_group_name = module.vpc.database_subnet_group_name
  environment          = "prod"
  multi_az             = true
  skip_final_snapshot  = false
  backup_retention_period = 7
  deletion_protection  = true
}

module "discount_db" {
  source = "../modules/rds"
  
  identifier           = "billing-discount-prod"
  allocated_storage    = 50
  engine_version       = "16.1"
  instance_class       = "db.t3.medium"
  db_name              = "discount_service"
  username             = var.db_username
  password             = var.db_password
  vpc_security_group_ids = [module.security.rds_sg_id]
  db_subnet_group_name = module.vpc.database_subnet_group_name
  environment          = "prod"
  multi_az             = true
  skip_final_snapshot  = false
  backup_retention_period = 7
  deletion_protection  = true
}

module "invoice_db" {
  source = "../modules/rds"
  
  identifier           = "billing-invoice-prod"
  allocated_storage    = 50
  engine_version       = "16.1"
  instance_class       = "db.t3.medium"
  db_name              = "invoice_service"
  username             = var.db_username
  password             = var.db_password
  vpc_security_group_ids = [module.security.rds_sg_id]
  db_subnet_group_name = module.vpc.database_subnet_group_name
  environment          = "prod"
  multi_az             = true
  skip_final_snapshot  = false
  backup_retention_period = 7
  deletion_protection  = true
}

module "payment_db" {
  source = "../modules/rds"
  
  identifier           = "billing-payment-prod"
  allocated_storage    = 50
  engine_version       = "16.1"
  instance_class       = "db.t3.medium"
  db_name              = "payment_service"
  username             = var.db_username
  password             = var.db_password
  vpc_security_group_ids = [module.security.rds_sg_id]
  db_subnet_group_name = module.vpc.database_subnet_group_name
  environment          = "prod"
  multi_az             = true
  skip_final_snapshot  = false
  backup_retention_period = 7
  deletion_protection  = true
}

# ECS Services
module "tax_service" {
  source = "../modules/ecs"
  
  service_name    = "tax-service"
  environment     = "prod"
  aws_region      = var.aws_region
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
  docker_image    = var.tax_service_image
  container_port  = 8001
  task_cpu        = 1024
  task_memory     = 2048
  desired_count   = 3
  assign_public_ip = false
  database_url    = "postgresql://${var.db_username}:${var.db_password}@${module.tax_db.db_instance_address}:5432/${module.tax_db.db_instance_name}"
  rabbitmq_url    = var.rabbitmq_url
  domain_name     = var.domain_name
  certificate_arn = var.certificate_arn
  ssm_parameter_prefix = "/billing/prod"
  sns_topic_arn  = module.monitoring.sns_topic_arn
  health_check_path = "/health"
  health_check_grace_period_seconds = 120
  autoscaling_enabled = true
  autoscaling_min_capacity = 3
  autoscaling_max_capacity = 10
  autoscaling_cpu_target = 70
}

module "discount_service" {
  source = "../modules/ecs"
  
  service_name    = "discount-service"
  environment     = "prod"
  aws_region      = var.aws_region
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
  docker_image    = var.discount_service_image
  container_port  = 8002
  task_cpu        = 1024
  task_memory     = 2048
  desired_count   = 3
  assign_public_ip = false
  database_url    = "postgresql://${var.db_username}:${var.db_password}@${module.discount_db.db_instance_address}:5432/${module.discount_db.db_instance_name}"
  rabbitmq_url    = var.rabbitmq_url
  domain_name     = var.domain_name
  certificate_arn = var.certificate_arn
  ssm_parameter_prefix = "/billing/prod"
  sns_topic_arn  = module.monitoring.sns_topic_arn
  health_check_path = "/health"
  health_check_grace_period_seconds = 120
  autoscaling_enabled = true
  autoscaling_min_capacity = 3
  autoscaling_max_capacity = 10
  autoscaling_cpu_target = 70
}

module "invoice_service" {
  source = "../modules/ecs"
  
  service_name    = "invoice-service"
  environment     = "prod"
  aws_region      = var.aws_region
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
  docker_image    = var.invoice_service_image
  container_port  = 8003
  task_cpu        = 1024
  task_memory     = 2048
  desired_count   = 3
  assign_public_ip = false
  database_url    = "postgresql://${var.db_username}:${var.db_password}@${module.invoice_db.db_instance_address}:5432/${module.invoice_db.db_instance_name}"
  rabbitmq_url    = var.rabbitmq_url
  domain_name     = var.domain_name
  certificate_arn = var.certificate_arn
  ssm_parameter_prefix = "/billing/prod"
  sns_topic_arn  = module.monitoring.sns_topic_arn
  health_check_path = "/health"
  health_check_grace_period_seconds = 120
  autoscaling_enabled = true
  autoscaling_min_capacity = 3
  autoscaling_max_capacity = 10
  autoscaling_cpu_target = 70
}

module "payment_service" {
  source = "../modules/ecs"
  
  service_name    = "payment-service"
  environment     = "prod"
  aws_region      = var.aws_region
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
  docker_image    = var.payment_service_image
  container_port  = 8004
  task_cpu        = 1024
  task_memory     = 2048
  desired_count   = 3
  assign_public_ip = false
  database_url    = "postgresql://${var.db_username}:${var.db_password}@${module.payment_db.db_instance_address}:5432/${module.payment_db.db_instance_name}"
  rabbitmq_url    = var.rabbitmq_url
  domain_name     = var.domain_name
  certificate_arn = var.certificate_arn
  ssm_parameter_prefix = "/billing/prod"
  sns_topic_arn  = module.monitoring.sns_topic_arn
  health_check_path = "/health"
  health_check_grace_period_seconds = 120
  autoscaling_enabled = true
  autoscaling_min_capacity = 3
  autoscaling_max_capacity = 10
  autoscaling_cpu_target = 70
}

# CloudWatch Alarms and Monitoring
module "monitoring" {
  source = "../modules/monitoring"
  
  environment = "prod"
  aws_region = var.aws_region
  rds_instances = [
    module.tax_db.db_instance_id,
    module.discount_db.db_instance_id,
    module.invoice_db.db_instance_id,
    module.payment_db.db_instance_id
  ]
  ecs_services = [
    "${module.tax_service.service_name}",
    "${module.discount_service.service_name}",
    "${module.invoice_service.service_name}",
    "${module.payment_service.service_name}"
  ]
  ecs_cluster_name = "billing-prod"
  alarm_email = var.alarm_email
}

# SSM Parameters for secrets
resource "aws_ssm_parameter" "jwt_public_key" {
  name      = "/billing/prod/jwt-public-key"
  type      = "SecureString"
  value     = var.jwt_public_key
  key_id    = module.security.kms_key_id
  overwrite = true
  
  tags = {
    Environment = "prod"
    Service     = "billing"
    Terraform   = "true"
  }
}
