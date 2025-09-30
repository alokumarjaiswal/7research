## Complete Step-by-Step Process: AWS Lambda SnapStart Research Setup

### **Step 1: VS Code Environment Setup** 
**What we did:** Set up development environment
**Actions:**
- Opened VS Code
- Installed Extensions:
  - Extension Pack for Java (by Microsoft)
  - AWS Toolkit (by Amazon Web Services)
  - CloudFormation Linter (by AWS CloudFormation)
- Restarted VS Code

### **Step 2: Project Structure Creation**
**What we did:** Created directory structure
**Commands/Actions:**
- Created folder: `lambda-snapstart-analysis`
- Opened in VS Code: File → Open Folder
- Created structure:
```
lambda-snapstart-analysis/
├── src/main/java/com/example/
├── pom.xml
└── README.md
```

### **Step 3: Maven Configuration**
**What we did:** Set up Maven dependencies
**File created:** `pom.xml`
**Content:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>lambda-snapstart-analysis</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    <properties>
        <maven.compiler.source>21</maven.compiler.source>
        <maven.compiler.target>21</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
    <dependencies>
        <dependency>
            <groupId>com.amazonaws</groupId>
            <artifactId>aws-lambda-java-core</artifactId>
            <version>1.2.3</version>
        </dependency>
        <dependency>
            <groupId>com.amazonaws</groupId>
            <artifactId>aws-lambda-java-events</artifactId>
            <version>3.11.3</version>
        </dependency>
        <dependency>
            <groupId>org.crac</groupId>
            <artifactId>crac</artifactId>
            <version>1.4.0</version>
        </dependency>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.15.2</version>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>3.4.1</version>
                <executions>
                    <execution>
                        <phase>package</phase>
                        <goals>
                            <goal>shade</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

### **Step 4: Baseline Lambda Function**
**What we did:** Created standard Lambda function
**File created:** `src/main/java/com/example/BaselineLambdaHandler.java`
**Content:** Complete Java class with 2-second initialization delay, business logic, and comprehensive response mapping

### **Step 5: SnapStart Lambda Function**  
**What we did:** Created SnapStart-optimized function
**File created:** `src/main/java/com/example/SnapStartLambdaHandler.java` (first version with CRaC)
**Issue encountered:** CRaC dependency caused NoClassDefFoundError
**Solution:** Created `SnapStartSimpleHandler.java` without CRaC dependency
**Final working content:** Java class with static initialization, preloaded data (10,000 items), and heavy computation

### **Step 6: Build Attempt**
**What we did:** Tried to compile project
**Commands attempted:**
```bash
mvn clean compile
mvn clean package
```
**Issue:** `mvn: The term 'mvn' is not recognized`
**Solution:** Used VS Code's built-in Java compilation (Ctrl+Shift+P → "Java: Reload Projects")
**Result:** VS Code automatically compiled classes to `target/classes/`

### **Step 7: AWS Credentials Setup**
**What we did:** Created AWS access keys and configured CLI
**Process:**
1. **AWS Console Setup:**
   - Navigated to IAM → Users
   - Created user: `lambda-developer`
   - Attached policies: AWSLambdaFullAccess, IAMReadOnlyAccess, CloudWatchFullAccess, AmazonAPIGatewayAdministrator
   - Created access keys for CLI access

2. **AWS CLI Installation & Configuration:**
   - Downloaded AWS CLI from aws.amazon.com/cli/
   - Ran installer
   - **Commands:**
   ```bash
   aws configure
   # Entered: Access Key ID, Secret Access Key, us-east-1, json
   aws sts get-caller-identity
   ```

### **Step 8: IAM Role Creation**
**What we did:** Created Lambda execution role
**Commands:**
```bash
aws iam create-role --role-name lambda-snapstart-execution-role --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

aws iam attach-role-policy --role-name lambda-snapstart-execution-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```
**Result:** Created role ARN: `arn:aws:iam::192153971334:role/lambda-snapstart-execution-role`

### **Step 9: Deployment Package Creation**
**What we did:** Built JAR file for deployment
**Commands:**
```bash
mkdir deployment
cd deployment
jar -cvf lambda-snapstart-analysis.jar -C ../target/classes .
cd ..
```

### **Step 10: Lambda Function Deployment**
**What we did:** Deployed both Lambda functions
**Commands:**
```bash
# Deploy baseline function (no SnapStart)
aws lambda create-function --function-name lambda-baseline --runtime java21 --role arn:aws:iam::192153971334:role/lambda-snapstart-execution-role --handler com.example.BaselineLambdaHandler --zip-file fileb://deployment/lambda-snapstart-analysis.jar --memory-size 1024 --timeout 30

# Deploy SnapStart function
aws lambda create-function --function-name lambda-snapstart --runtime java21 --role arn:aws:iam::192153971334:role/lambda-snapstart-execution-role --handler com.example.SnapStartLambdaHandler --zip-file fileb://deployment/lambda-snapstart-analysis.jar --memory-size 1024 --timeout 30 --snap-start ApplyOn=PublishedVersions

# Publish version for SnapStart
aws lambda publish-version --function-name lambda-snapstart

# Verify deployment
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `lambda-`)].[FunctionName,Runtime,State]' --output table
```

### **Step 11: Function Testing**
**What we did:** Tested both functions
**Commands:**
```bash
# Test baseline function
aws lambda invoke --function-name lambda-baseline baseline-response.json

# Check response
type baseline-response.json
```
**Result:** Baseline worked successfully

**SnapStart function issue:**
```bash
aws lambda invoke --function-name lambda-snapstart snapstart-response.json
```
**Error:** `NoClassDefFoundError: org/crac/Resource`

**Fix applied:**
- Updated SnapStart function handler to use `SnapStartSimpleHandler`
- Rebuilt JAR and updated function:
```bash
jar -cvf deployment/lambda-snapstart-analysis.jar -C target/classes .
aws lambda update-function-code --function-name lambda-snapstart --zip-file fileb://deployment/lambda-snapstart-analysis.jar
aws lambda update-function-configuration --function-name lambda-snapstart --handler com.example.SnapStartSimpleHandler
aws lambda invoke --function-name lambda-snapstart snapstart-fixed.json
```

### **Step 12: CloudWatch Dashboard**
**What we did:** Created monitoring dashboard
**File created:** `cloudwatch-dashboard.json`
**Command:**
```bash
aws cloudwatch put-dashboard --dashboard-name "Lambda-SnapStart-Performance" --dashboard-body file://cloudwatch-dashboard.json
```

### **Step 13: Performance Testing Script**
**What we did:** Created automated testing
**File created:** `performance-test.ps1`
**Command:**
```bash
powershell -ExecutionPolicy Bypass -File performance-test.ps1
```

### **Step 14: Performance Test Execution**
**What we ran:** Comprehensive performance comparison
**Results achieved:**
```
Baseline Lambda Average: 6,711.09ms
SnapStart Lambda Average: 5,330.22ms  
Performance Improvement: 20.6%
Time Reduction: 1,380.87ms
```

### **Step 15: Documentation Creation**
**What we created:**
1. **research-summary.md** - Markdown research report
2. **Complete LaTeX document** for Overleaf
3. **Comprehensive README.md** - Technical documentation

### **Key Commands Summary:**
```bash
# Project setup (VS Code GUI actions)
# AWS CLI configuration
aws configure
aws sts get-caller-identity

# IAM role creation
aws iam create-role --role-name lambda-snapstart-execution-role --assume-role-policy-document '{...}'
aws iam attach-role-policy --role-name lambda-snapstart-execution-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Build deployment
jar -cvf deployment/lambda-snapstart-analysis.jar -C target/classes .

# Deploy functions
aws lambda create-function --function-name lambda-baseline [parameters]
aws lambda create-function --function-name lambda-snapstart [parameters] --snap-start ApplyOn=PublishedVersions
aws lambda publish-version --function-name lambda-snapstart

# Test functions
aws lambda invoke --function-name lambda-baseline baseline-response.json
aws lambda invoke --function-name lambda-snapstart snapstart-response.json

# Fix and update
aws lambda update-function-code --function-name lambda-snapstart --zip-file fileb://deployment/lambda-snapstart-analysis.jar
aws lambda update-function-configuration --function-name lambda-snapstart --handler com.example.SnapStartSimpleHandler

# Monitoring and testing
aws cloudwatch put-dashboard --dashboard-name "Lambda-SnapStart-Performance" --dashboard-body file://cloudwatch-dashboard.json
powershell -ExecutionPolicy Bypass -File performance-test.ps1
```

**Final Achievement:** Successfully demonstrated 20.6% performance improvement with complete research documentation and reproducible infrastructure.

[1](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)
[2](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html)
[3](https://aws.amazon.com/blogs/compute/using-aws-lambda-snapstart-with-infrastructure-as-code-and-ci-cd-pipelines/)
[4](https://www.cloudthat.com/resources/blog/implementing-aws-lambda-snapstart-with-java-application-logic/)
[5](https://dev.to/aws-builders/efficiently-handling-high-concurrency-with-aws-lambda-snapstart-a-step-by-step-guide-2m81)
[6](https://www.rahulpnath.com/blog/aws-lambda-snapstart/)
[7](https://aws.amazon.com/blogs/compute/optimizing-cold-start-performance-of-aws-lambda-using-advanced-priming-strategies-with-snapstart/)
[8](https://www.youtube.com/watch?v=2m-lNBDpvKk)
[9](https://aws.amazon.com/blogs/compute/debugging-snapstart-enabled-lambda-functions-made-easy-with-aws-x-ray/)