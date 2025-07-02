output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.billing.dashboard_name
}

output "log_groups" {
  description = "Map of service names to their CloudWatch log group ARNs"
  value       = { for i, service in var.ecs_services : service => aws_cloudwatch_log_group.ecs_services[i].arn }
}
