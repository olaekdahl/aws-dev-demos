resource "aws_dynamodb_table" "quizzes" {
  name         = "${local.name}-quizzes"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "quizId"

  attribute {
    name = "quizId"
    type = "S"
  }

  point_in_time_recovery { enabled = true }

  server_side_encryption { enabled = true }

  tags = local.tags
}

resource "aws_dynamodb_table" "attempts" {
  name         = "${local.name}-attempts"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "attemptId"

  attribute {
    name = "attemptId"
    type = "S"
  }

  point_in_time_recovery { enabled = true }

  server_side_encryption { enabled = true }

  tags = local.tags
}

resource "aws_dynamodb_table" "exports" {
  name         = "${local.name}-exports"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "exportId"

  attribute {
    name = "exportId"
    type = "S"
  }

  point_in_time_recovery { enabled = true }

  server_side_encryption { enabled = true }

  tags = local.tags
}
