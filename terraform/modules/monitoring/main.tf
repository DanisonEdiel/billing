resource "aws_sns_topic" "alerts" {
  name = "billing-${var.environment}-alerts"
  
  tags = {
    Name        = "billing-${var.environment}-alerts"
    Environment = var.environment
    Terraform   = "true"
  }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# RDS Alarms
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  count               = length(var.rds_instances)
  alarm_name          = "billing-${var.environment}-${element(var.rds_instances, count.index)}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    DBInstanceIdentifier = element(var.rds_instances, count.index)
  }
  
  tags = {
    Name        = "billing-${var.environment}-${element(var.rds_instances, count.index)}-high-cpu"
    Environment = var.environment
    Terraform   = "true"
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_memory" {
  count               = length(var.rds_instances)
  alarm_name          = "billing-${var.environment}-${element(var.rds_instances, count.index)}-low-memory"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "FreeableMemory"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "100000000" # 100MB in bytes
  alarm_description   = "This metric monitors RDS freeable memory"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    DBInstanceIdentifier = element(var.rds_instances, count.index)
  }
  
  tags = {
    Name        = "billing-${var.environment}-${element(var.rds_instances, count.index)}-low-memory"
    Environment = var.environment
    Terraform   = "true"
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  count               = length(var.rds_instances)
  alarm_name          = "billing-${var.environment}-${element(var.rds_instances, count.index)}-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "5000000000" # 5GB in bytes
  alarm_description   = "This metric monitors RDS free storage space"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    DBInstanceIdentifier = element(var.rds_instances, count.index)
  }
  
  tags = {
    Name        = "billing-${var.environment}-${element(var.rds_instances, count.index)}-low-storage"
    Environment = var.environment
    Terraform   = "true"
  }
}

# ECS Alarms
resource "aws_cloudwatch_metric_alarm" "ecs_cpu" {
  count               = length(var.ecs_services)
  alarm_name          = "billing-${var.environment}-${element(var.ecs_services, count.index)}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS service CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = element(var.ecs_services, count.index)
  }
  
  tags = {
    Name        = "billing-${var.environment}-${element(var.ecs_services, count.index)}-high-cpu"
    Environment = var.environment
    Terraform   = "true"
  }
}

resource "aws_cloudwatch_metric_alarm" "ecs_memory" {
  count               = length(var.ecs_services)
  alarm_name          = "billing-${var.environment}-${element(var.ecs_services, count.index)}-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS service memory utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = element(var.ecs_services, count.index)
  }
  
  tags = {
    Name        = "billing-${var.environment}-${element(var.ecs_services, count.index)}-high-memory"
    Environment = var.environment
    Terraform   = "true"
  }
}

# Dashboard for all services
resource "aws_cloudwatch_dashboard" "billing" {
  dashboard_name = "billing-${var.environment}"
  
  dashboard_body = jsonencode({
    widgets = concat(
      # RDS CPU Widgets
      [
        for i, instance in var.rds_instances : {
          type   = "metric"
          x      = (i % 2) * 12
          y      = floor(i / 2) * 6
          width  = 12
          height = 6
          properties = {
            metrics = [
              ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", instance]
            ]
            period = 300
            stat   = "Average"
            region = var.aws_region
            title  = "${instance} - CPU Utilization"
          }
        }
      ],
      # ECS CPU Widgets
      [
        for i, service in var.ecs_services : {
          type   = "metric"
          x      = (i % 2) * 12
          y      = floor((i + length(var.rds_instances)) / 2) * 6
          width  = 12
          height = 6
          properties = {
            metrics = [
              ["AWS/ECS", "CPUUtilization", "ClusterName", var.ecs_cluster_name, "ServiceName", service]
            ]
            period = 300
            stat   = "Average"
            region = var.aws_region
            title  = "${service} - CPU Utilization"
          }
        }
      ],
      # ECS Memory Widgets
      [
        for i, service in var.ecs_services : {
          type   = "metric"
          x      = (i % 2) * 12
          y      = floor((i + length(var.rds_instances) + length(var.ecs_services)) / 2) * 6
          width  = 12
          height = 6
          properties = {
            metrics = [
              ["AWS/ECS", "MemoryUtilization", "ClusterName", var.ecs_cluster_name, "ServiceName", service]
            ]
            period = 300
            stat   = "Average"
            region = var.aws_region
            title  = "${service} - Memory Utilization"
          }
        }
      ]
    )
  })
}

# Log Groups for CloudWatch Logs
resource "aws_cloudwatch_log_group" "ecs_services" {
  count             = length(var.ecs_services)
  name              = "/ecs/${var.ecs_cluster_name}/${element(var.ecs_services, count.index)}"
  retention_in_days = var.environment == "prod" ? 30 : 7
  
  tags = {
    Name        = "/ecs/${var.ecs_cluster_name}/${element(var.ecs_services, count.index)}"
    Environment = var.environment
    Service     = element(var.ecs_services, count.index)
    Terraform   = "true"
  }
}

# Metric Filters for Error Logs
resource "aws_cloudwatch_log_metric_filter" "error_logs" {
  count          = length(var.ecs_services)
  name           = "billing-${var.environment}-${element(var.ecs_services, count.index)}-errors"
  pattern        = "ERROR"
  log_group_name = aws_cloudwatch_log_group.ecs_services[count.index].name
  
  metric_transformation {
    name      = "ErrorCount"
    namespace = "Billing/Services"
    value     = "1"
    dimensions = {
      Service     = element(var.ecs_services, count.index)
      Environment = var.environment
    }
  }
}

# Alarms for Error Logs
resource "aws_cloudwatch_metric_alarm" "error_logs" {
  count               = length(var.ecs_services)
  alarm_name          = "billing-${var.environment}-${element(var.ecs_services, count.index)}-error-logs"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ErrorCount"
  namespace           = "Billing/Services"
  period              = "60"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors error logs in the service"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    Service     = element(var.ecs_services, count.index)
    Environment = var.environment
  }
  
  tags = {
    Name        = "billing-${var.environment}-${element(var.ecs_services, count.index)}-error-logs"
    Environment = var.environment
    Service     = element(var.ecs_services, count.index)
    Terraform   = "true"
  }
}
