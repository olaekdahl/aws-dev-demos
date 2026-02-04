resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "capstone-vpc" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "capstone-igw" }
}

# Public subnets (one per AZ) + route tables + NAT per AZ
resource "aws_subnet" "public" {
  for_each                = { for idx, az in local.selected_azs : idx => az }
  vpc_id                  = aws_vpc.main.id
  availability_zone       = each.value
  cidr_block              = var.public_subnet_cidrs[tonumber(each.key)]
  map_public_ip_on_launch = true
  tags                    = { Name = "public-${each.value}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "public-rt" }
}

resource "aws_route" "public_inet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
}

resource "aws_route_table_association" "public_assoc" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

# One NAT Gateway per AZ
resource "aws_eip" "nat" {
  for_each = aws_subnet.public
  domain   = "vpc"
  tags     = { Name = "nat-eip-${each.key}" }
}

resource "aws_nat_gateway" "nat" {
  for_each      = aws_subnet.public
  subnet_id     = each.value.id
  allocation_id = aws_eip.nat[each.key].id
  tags          = { Name = "nat-${each.key}" }
}

# Private APP subnets (route via NAT)
resource "aws_subnet" "app" {
  for_each          = { for idx, az in local.selected_azs : idx => az }
  vpc_id            = aws_vpc.main.id
  availability_zone = each.value
  cidr_block        = var.app_subnet_cidrs[tonumber(each.key)]
  tags              = { Name = "app-${each.value}" }
}

resource "aws_route_table" "app" {
  for_each = aws_subnet.app
  vpc_id   = aws_vpc.main.id
  tags     = { Name = "app-rt-${each.key}" }
}

resource "aws_route" "app_egress" {
  for_each               = aws_route_table.app
  route_table_id         = each.value.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.nat[each.key].id
}

resource "aws_route_table_association" "app_assoc" {
  for_each       = aws_subnet.app
  subnet_id      = each.value.id
  route_table_id = aws_route_table.app[each.key].id
}

# Private DB subnets (no egress)
resource "aws_subnet" "db" {
  for_each          = { for idx, az in local.selected_azs : idx => az }
  vpc_id            = aws_vpc.main.id
  availability_zone = each.value
  cidr_block        = var.db_subnet_cidrs[tonumber(each.key)]
  tags              = { Name = "db-${each.value}" }
}

resource "aws_db_subnet_group" "aurora" {
  name       = "aurora-subnets"
  subnet_ids = [for s in aws_subnet.db : s.id]
}