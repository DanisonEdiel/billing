resource "aws_ecs_cluster" "billing_cluster" {
  name = "billing-${var.environment}"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Name        = "billing-${var.environment}"
    Environment = var.environment
    Terraform   = "true"
  }
}

resource "aws_ecs_task_definition" "service_task" {
  family                   = "${var.service_name}-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  
  container_definitions = jsonencode([
    {
      name      = var.service_name
      image     = var.docker_image
      essential = true
      
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "DATABASE_URL"
          value = var.database_url
        },
        {
          name  = "RABBITMQ_URL"
          value = var.rabbitmq_url
        },
        {
          name  = "SERVICE_NAME"
          value = var.service_name
        },
        {
          name  = "LOG_LEVEL"
          value = "INFO"
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]
      
      secrets = [
        {
          name      = "JWT_PUBLIC_KEY"
          valueFrom = "${var.ssm_parameter_prefix}/jwt-public-key"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.service_name}-${var.environment}"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
  
  tags = {
    Name        = "${var.service_name}-${var.environment}"
    Environment = var.environment
    Service     = var.service_name
    Terraform   = "true"
  }
}

resource "aws_ecs_service" "service" {
  name                               = var.service_name
  cluster                            = aws_ecs_cluster.billing_cluster.id
  task_definition                    = aws_ecs_task_definition.service_task.arn
  desired_count                      = var.desired_count
  launch_type                        = "FARGATE"
  scheduling_strategy                = "REPLICA"
  health_check_grace_period_seconds  = 60
  
  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.ecs_service.id]
    assign_public_ip = var.assign_public_ip
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.service.arn
    container_name   = var.service_name
    container_port   = var.container_port
  }
  
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  
  deployment_controller {
    type = "ECS"
  }
  
  tags = {
    Name        = "${var.service_name}-${var.environment}"
    Environment = var.environment
    Service     = var.service_name
    Terraform   = "true"
  }
  
  depends_on = [aws_lb_listener_rule.service]
}

resource "aws_security_group" "ecs_service" {
  name        = "${var.service_name}-${var.environment}-ecs-sg"
  description = "Security group for ${var.service_name} ECS service"
  vpc_id      = var.vpc_id
  
  ingress {
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name        = "${var.service_name}-${var.environment}-ecs-sg"
    Environment = var.environment
    Service     = var.service_name
    Terraform   = "true"
  }
}

resource "aws_lb" "service" {
  name               = "${var.service_name}-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.subnet_ids
  
  enable_deletion_protection = var.environment == "prod" ? true : false
  
  tags = {
    Name        = "${var.service_name}-${var.environment}"
    Environment = var.environment
    Service     = var.service_name
    Terraform   = "true"
  }
}

resource "aws_security_group" "alb" {
  name        = "${var.service_name}-${var.environment}-alb-sg"
  description = "Security group for ${var.service_name} ALB"
  vpc_id      = var.vpc_id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name        = "${var.service_name}-${var.environment}-alb-sg"
    Environment = var.environment
    Service     = var.service_name
    Terraform   = "true"
  }
}

resource "aws_lb_target_group" "service" {
  name        = "${var.service_name}-${var.environment}"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    enabled             = true
    interval            = 30
    path                = "/health"
    port                = "traffic-port"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    matcher             = "200"
  }
  
  tags = {
    Name        = "${var.service_name}-${var.environment}"
    Environment = var.environment
    Service     = var.service_name
    Terraform   = "true"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.service.arn
  port              = 80
  protocol          = "HTTP"
  
  default_action {
    type = "redirect"
    
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.service.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.certificate_arn
  
  default_action {
    type = "fixed-response"
    
    fixed_response {
      content_type = "text/plain"
      message_body = "Service not found"
      status_code  = "404"
    }
  }
}

resource "aws_lb_listener_rule" "service" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.service.arn
  }
  
  condition {
    host_header {
      values = ["${var.service_name}.${var.domain_name}"]
    }
  }
}

resource "aws_cloudwatch_log_group" "service" {
  name              = "/ecs/${var.service_name}-${var.environment}"
  retention_in_days = var.environment == "prod" ? 30 : 7
  
  tags = {
    Name        = "/ecs/${var.service_name}-${var.environment}"
    Environment = var.environment
    Service     = var.service_name
    Terraform   = "true"
  }
}

resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.service_name}-${var.environment}-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name        = "${var.service_name}-${var.environment}-execution-role"
    Environment = var.environment
    Service     = var.service_name
    Terraform   = "true"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_execution_ssm" {
  name = "${var.service_name}-${var.environment}-ssm-policy"
  role = aws_iam_role.ecs_execution_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ssm:GetParameters",
          "secretsmanager:GetSecretValue",
          "kms:Decrypt"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "ecs_task_role" {
  name = "${var.service_name}-${var.environment}-task-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name        = "${var.service_name}-${var.environment}-task-role"
    Environment = var.environment
    Service     = var.service_name
    Terraform   = "true"
  }
}

resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${var.service_name}-${var.environment}-task-policy"
  role = aws_iam_role.ecs_task_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "${aws_cloudwatch_log_group.service.arn}:*"
      }
    ]
  })
}

resource "aws_cloudwatch_metric_alarm" "service_cpu" {
  alarm_name          = "${var.service_name}-${var.environment}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS service CPU utilization"
  alarm_actions       = [var.sns_topic_arn]
  ok_actions          = [var.sns_topic_arn]
  
  dimensions = {
    ClusterName = aws_ecs_cluster.billing_cluster.name
    ServiceName = aws_ecs_service.service.name
  }
  
  tags = {
    Name        = "${var.service_name}-${var.environment}-high-cpu"
    Environment = var.environment
    Service     = var.service_name
    Terraform   = "true"
  }
}

resource "aws_cloudwatch_metric_alarm" "service_memory" {
  alarm_name          = "${var.service_name}-${var.environment}-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS service memory utilization"
  alarm_actions       = [var.sns_topic_arn]
  ok_actions          = [var.sns_topic_arn]
  
  dimensions = {
    ClusterName = aws_ecs_cluster.billing_cluster.name
    ServiceName = aws_ecs_service.service.name
  }
  
  tags = {
    Name        = "${var.service_name}-${var.environment}-high-memory"
    Environment = var.environment
    Service     = var.service_name
    Terraform   = "true"
  }
}
