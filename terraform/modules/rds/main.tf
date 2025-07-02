resource "aws_db_instance" "postgres" {
  identifier             = var.identifier
  allocated_storage      = var.allocated_storage
  engine                 = "postgres"
  engine_version         = var.engine_version
  instance_class         = var.instance_class
  db_name                = var.db_name
  username               = var.username
  password               = var.password
  parameter_group_name   = aws_db_parameter_group.postgres.name
  vpc_security_group_ids = var.vpc_security_group_ids
  db_subnet_group_name   = var.db_subnet_group_name
  skip_final_snapshot    = var.skip_final_snapshot
  multi_az               = var.multi_az
  backup_retention_period = var.environment == "prod" ? 7 : 1
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"
  storage_encrypted      = true
  deletion_protection    = var.environment == "prod" ? true : false
  
  tags = {
    Name        = "${var.identifier}"
    Environment = var.environment
    Service     = var.db_name
    Terraform   = "true"
  }
}

resource "aws_db_parameter_group" "postgres" {
  name   = "${var.identifier}-pg16"
  family = "postgres16"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_statement"
    value = "ddl"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "pg_stat_statements.track"
    value = "all"
  }

  tags = {
    Name        = "${var.identifier}-pg16"
    Environment = var.environment
    Service     = var.db_name
    Terraform   = "true"
  }
}

resource "aws_cloudwatch_metric_alarm" "db_cpu" {
  alarm_name          = "${var.identifier}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = [var.sns_topic_arn]
  ok_actions          = [var.sns_topic_arn]
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }
  
  tags = {
    Name        = "${var.identifier}-high-cpu"
    Environment = var.environment
    Service     = var.db_name
    Terraform   = "true"
  }
}

resource "aws_cloudwatch_metric_alarm" "db_memory" {
  alarm_name          = "${var.identifier}-low-memory"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "FreeableMemory"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "100000000" # 100MB in bytes
  alarm_description   = "This metric monitors RDS freeable memory"
  alarm_actions       = [var.sns_topic_arn]
  ok_actions          = [var.sns_topic_arn]
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }
  
  tags = {
    Name        = "${var.identifier}-low-memory"
    Environment = var.environment
    Service     = var.db_name
    Terraform   = "true"
  }
}

resource "aws_cloudwatch_metric_alarm" "db_storage" {
  alarm_name          = "${var.identifier}-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "5000000000" # 5GB in bytes
  alarm_description   = "This metric monitors RDS free storage space"
  alarm_actions       = [var.sns_topic_arn]
  ok_actions          = [var.sns_topic_arn]
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }
  
  tags = {
    Name        = "${var.identifier}-low-storage"
    Environment = var.environment
    Service     = var.db_name
    Terraform   = "true"
  }
}
