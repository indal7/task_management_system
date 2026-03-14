from app import create_app, db
from app.models.user import User
from app.models.enums import TaskPriority, UserRole, TaskStatus, ProjectStatus, NotificationType, TaskType, SprintStatus
from app.models.task import Task
from app.models.project import Project
from app.models.task_comment import TaskComment
from app.models.notification import Notification
from app.models.sprint import Sprint
from app.models.project_member import ProjectMember
from app.models.time_log import TimeLog
from datetime import datetime, timedelta, UTC
import json
import random

# Create Flask app instance
app = create_app('dev')

# Run within application context
with app.app_context():
    try:
        print("🧹 Clearing existing data...")
        # Clear in proper order to avoid foreign key constraints
        db.session.query(TimeLog).delete()
        db.session.query(Notification).delete()
        db.session.query(TaskComment).delete()
        db.session.query(Task).delete()
        db.session.query(ProjectMember).delete()
        db.session.query(Sprint).delete()
        db.session.query(Project).delete()
        db.session.query(User).delete()
        db.session.commit()
        print("✅ Existing data cleared")
    except Exception as e:
        print(f"⚠️  Warning: Could not clear existing data: {e}")
        db.session.rollback()

    # ===== USERS =====
    try:
        print("👥 Creating users...")
        # Core team
        admin = User.register(
            name="Admin User", 
            email="admin@example.com", 
            password="admin123", 
            role=UserRole.ADMIN
        )
        admin.bio = "System administrator with 10+ years of experience"
        admin.skills = json.dumps(["System Administration", "DevOps", "Security", "Database Management"])
        admin.github_username = "admin_user"
        admin.timezone = "UTC"
        admin.daily_work_hours = 8.0

        manager = User.register(
            name="Sarah Johnson", 
            email="manager@example.com", 
            password="manager123", 
            role=UserRole.PROJECT_MANAGER
        )
        manager.bio = "Experienced project manager specializing in agile methodologies"
        manager.skills = json.dumps(["Project Management", "Agile", "Scrum", "Team Leadership", "Risk Management"])
        manager.github_username = "sarah_pm"
        manager.linkedin_url = "https://linkedin.com/in/sarah-johnson"
        manager.timezone = "EST"
        manager.daily_work_hours = 8.0

        team_lead = User.register(
            name="Michael Chen", 
            email="teamlead@example.com", 
            password="lead123", 
            role=UserRole.TEAM_LEAD
        )
        team_lead.bio = "Technical team lead with expertise in full-stack development"
        team_lead.skills = json.dumps(["Team Leadership", "Full Stack Development", "Architecture", "Code Review", "Mentoring"])
        team_lead.github_username = "michael_chen"
        team_lead.timezone = "PST"
        team_lead.daily_work_hours = 8.0

        indal = User.register(
            name="Indal Saroj", 
            email="indalsaroj404@gmail.com", 
            password="123456789", 
            role=UserRole.SENIOR_DEVELOPER
        )
        indal.bio = "Senior full-stack developer passionate about clean code and modern technologies"
        indal.skills = json.dumps(["Python", "JavaScript", "React", "Flask", "PostgreSQL", "Docker", "AWS", "UI/UX Design"])
        indal.github_username = "indalsaroj404"
        indal.linkedin_url = "https://linkedin.com/in/indal-saroj"
        indal.timezone = "IST"
        indal.daily_work_hours = 8.0
        indal.hourly_rate = 75.0

        emp1 = User.register(
            name="John Doe", 
            email="john@example.com", 
            password="john123", 
            role=UserRole.DEVELOPER
        )
        emp1.bio = "Backend developer with strong problem-solving skills"
        emp1.skills = json.dumps(["Python", "Django", "PostgreSQL", "REST APIs", "Git", "Linux"])
        emp1.github_username = "johndoe_dev"
        emp1.timezone = "EST"
        emp1.daily_work_hours = 8.0
        emp1.hourly_rate = 60.0

        emp2 = User.register(
            name="Jane Smith", 
            email="jane@example.com", 
            password="jane123", 
            role=UserRole.QA_ENGINEER
        )
        emp2.bio = "Quality assurance engineer focused on automation and testing strategies"
        emp2.skills = json.dumps(["Test Automation", "Selenium", "Python", "Manual Testing", "Bug Tracking", "Performance Testing"])
        emp2.github_username = "jane_qa"
        emp2.timezone = "PST"
        emp2.daily_work_hours = 8.0
        emp2.hourly_rate = 55.0

        # Additional team members
        designer = User.register(
            name="Emily Rodriguez", 
            email="emily@example.com", 
            password="emily123", 
            role=UserRole.UI_UX_DESIGNER
        )
        designer.bio = "Creative UI/UX designer with a passion for user-centered design"
        designer.skills = json.dumps(["UI Design", "UX Research", "Figma", "Adobe Creative Suite", "Prototyping", "User Testing"])
        designer.github_username = "emily_design"
        designer.timezone = "MST"
        designer.daily_work_hours = 8.0
        designer.hourly_rate = 65.0

        devops = User.register(
            name="Alex Thompson", 
            email="alex@example.com", 
            password="alex123", 
            role=UserRole.DEVOPS_ENGINEER
        )
        devops.bio = "DevOps engineer specializing in cloud infrastructure and automation"
        devops.skills = json.dumps(["AWS", "Docker", "Kubernetes", "CI/CD", "Terraform", "Monitoring", "Linux"])
        devops.github_username = "alex_devops"
        devops.timezone = "UTC"
        devops.daily_work_hours = 8.0
        devops.hourly_rate = 80.0

        analyst = User.register(
            name="Lisa Wang", 
            email="lisa@example.com", 
            password="lisa123", 
            role=UserRole.BUSINESS_ANALYST
        )
        analyst.bio = "Business analyst bridging the gap between business and technology"
        analyst.skills = json.dumps(["Business Analysis", "Requirements Gathering", "Process Modeling", "SQL", "Data Analysis"])
        analyst.github_username = "lisa_analyst"
        analyst.timezone = "EST"
        analyst.daily_work_hours = 8.0
        analyst.hourly_rate = 70.0

        db.session.add_all([admin, manager, team_lead, indal, emp1, emp2, designer, devops, analyst])
        db.session.commit()
        print("✅ Users created: 9")
    except ValueError as e:
        print(f"❌ User creation error: {e}")
        db.session.rollback()
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected error creating users: {e}")
        db.session.rollback()
        exit(1)

    # ===== PROJECTS =====
    try:
        print("📁 Creating projects...")
        # Create projects without repository_url and documentation_url initially
        project1 = Project(
            name="E-Commerce Platform Redesign", 
            description="Complete redesign of the company's e-commerce platform with modern UI/UX and improved performance", 
            owner_id=manager.id, 
            status=ProjectStatus.ACTIVE,
            start_date=datetime.now(UTC) - timedelta(days=30),
            end_date=datetime.now(UTC) + timedelta(days=60),
            estimated_hours=800.0,
            technology_stack=json.dumps(["React", "Node.js", "PostgreSQL", "Redis", "AWS"]),
            client_name="Tech Corp Inc.",
            client_email="client@techcorp.com"
        )

        project2 = Project(
            name="Mobile App Development", 
            description="Native mobile application for iOS and Android platforms with real-time features", 
            owner_id=team_lead.id, 
            status=ProjectStatus.ACTIVE,
            start_date=datetime.now(UTC) - timedelta(days=20),
            end_date=datetime.now(UTC) + timedelta(days=90),
            estimated_hours=1200.0,
            technology_stack=json.dumps(["React Native", "Firebase", "Node.js", "MongoDB"]),
            client_name="StartupXYZ",
            client_email="contact@startupxyz.com"
        )

        project3 = Project(
            name="Database Migration & Optimization", 
            description="Migrate legacy database to cloud infrastructure with performance optimization", 
            owner_id=admin.id, 
            status=ProjectStatus.COMPLETED,
            start_date=datetime.now(UTC) - timedelta(days=90),
            end_date=datetime.now(UTC) - timedelta(days=10),
            estimated_hours=400.0,
            technology_stack=json.dumps(["PostgreSQL", "AWS RDS", "Docker", "Python"])
        )

        project4 = Project(
            name="Internal Admin Dashboard", 
            description="Comprehensive admin dashboard for internal analytics, user management, and reporting", 
            owner_id=indal.id, 
            status=ProjectStatus.ACTIVE,
            start_date=datetime.now(UTC) - timedelta(days=15),
            end_date=datetime.now(UTC) + timedelta(days=45),
            estimated_hours=600.0,
            technology_stack=json.dumps(["Flask", "React", "PostgreSQL", "Chart.js", "Docker"])
        )

        project5 = Project(
            name="Client Feedback System", 
            description="Advanced feedback collection and analysis system with AI-powered insights", 
            owner_id=analyst.id, 
            status=ProjectStatus.ON_HOLD,
            start_date=datetime.now(UTC) + timedelta(days=30),
            end_date=datetime.now(UTC) + timedelta(days=120),
            estimated_hours=500.0,
            technology_stack=json.dumps(["Python", "FastAPI", "PostgreSQL", "Machine Learning", "React"])
        )

        project6 = Project(
            name="DevOps Infrastructure Setup", 
            description="Complete CI/CD pipeline setup with monitoring and automated deployments", 
            owner_id=devops.id, 
            status=ProjectStatus.ACTIVE,
            start_date=datetime.now(UTC) - timedelta(days=10),
            end_date=datetime.now(UTC) + timedelta(days=30),
            estimated_hours=300.0,
            technology_stack=json.dumps(["Docker", "Kubernetes", "Jenkins", "AWS", "Terraform", "Prometheus"])
        )

        # Add projects to session and commit
        db.session.add_all([project1, project2, project3, project4, project5, project6])
        db.session.commit()
        
        # Now update with repository and documentation URLs if the columns exist
        try:
            project1.repository_url = "https://github.com/company/ecommerce-platform"
            project1.documentation_url = "https://docs.company.com/ecommerce"
            project2.repository_url = "https://github.com/startupxyz/mobile-app"
            project2.documentation_url = "https://docs.startupxyz.com/mobile"
            project3.repository_url = "https://github.com/company/db-migration"
            project4.repository_url = "https://github.com/company/admin-dashboard"
            project6.repository_url = "https://github.com/company/devops-infrastructure"
            db.session.commit()
            print("✅ Projects created with URLs: 6")
        except Exception as url_error:
            print(f"⚠️  Projects created without URLs (columns may not exist): {url_error}")
            print("✅ Projects created: 6")
            
    except Exception as e:
        print(f"❌ Error creating projects: {e}")
        db.session.rollback()
        exit(1)

    # ===== PROJECT MEMBERS =====
    try:
        print("👥 Adding project members...")
        project_members = [
            # E-Commerce Platform team
            ProjectMember(project_id=project1.id, user_id=indal.id, role="Senior Developer", can_manage_sprints=True),
            ProjectMember(project_id=project1.id, user_id=emp1.id, role="Backend Developer"),
            ProjectMember(project_id=project1.id, user_id=designer.id, role="UI/UX Designer"),
            ProjectMember(project_id=project1.id, user_id=emp2.id, role="QA Engineer"),
            
            # Mobile App team
            ProjectMember(project_id=project2.id, user_id=indal.id, role="Technical Consultant"),
            ProjectMember(project_id=project2.id, user_id=emp1.id, role="Mobile Developer"),
            ProjectMember(project_id=project2.id, user_id=designer.id, role="Mobile UI Designer"),
            
            # Database Migration team
            ProjectMember(project_id=project3.id, user_id=devops.id, role="DevOps Lead", can_manage_sprints=True),
            ProjectMember(project_id=project3.id, user_id=emp1.id, role="Database Developer"),
            
            # Admin Dashboard team
            ProjectMember(project_id=project4.id, user_id=emp1.id, role="Backend Developer"),
            ProjectMember(project_id=project4.id, user_id=designer.id, role="Frontend Designer"),
            ProjectMember(project_id=project4.id, user_id=analyst.id, role="Business Analyst"),
            
            # DevOps Infrastructure team
            ProjectMember(project_id=project6.id, user_id=team_lead.id, role="Technical Advisor"),
            ProjectMember(project_id=project6.id, user_id=emp1.id, role="Developer"),
        ]
        
        db.session.add_all(project_members)
        db.session.commit()
        print("✅ Project members added")
    except Exception as e:
        print(f"❌ Error adding project members: {e}")
        db.session.rollback()
        exit(1)

    # ===== SPRINTS =====
    try:
        print("🏃 Creating sprints...")
        # Sprint for E-Commerce Platform
        sprint1 = Sprint(
            name="E-Commerce Sprint 1 - Foundation",
            description="Setup project foundation, basic authentication, and database schema",
            project_id=project1.id,
            status=SprintStatus.COMPLETED,
            start_date=datetime.now(UTC) - timedelta(days=28),
            end_date=datetime.now(UTC) - timedelta(days=14),
            goal="Establish solid project foundation and core functionality",
            capacity_hours=160.0,
            velocity_points=25
        )

        sprint2 = Sprint(
            name="E-Commerce Sprint 2 - Core Features",
            description="Implement product catalog, shopping cart, and checkout process",
            project_id=project1.id,
            status=SprintStatus.ACTIVE,
            start_date=datetime.now(UTC) - timedelta(days=14),
            end_date=datetime.now(UTC),
            goal="Deliver core e-commerce functionality",
            capacity_hours=160.0,
            velocity_points=30
        )

        # Sprint for Mobile App
        sprint3 = Sprint(
            name="Mobile App Sprint 1 - Setup",
            description="Project setup, navigation, and basic UI components",
            project_id=project2.id,
            status=SprintStatus.ACTIVE,
            start_date=datetime.now(UTC) - timedelta(days=14),
            end_date=datetime.now(UTC),
            goal="Setup mobile app foundation",
            capacity_hours=120.0,
            velocity_points=20
        )

        # Sprint for Admin Dashboard
        sprint4 = Sprint(
            name="Dashboard Sprint 1 - Core Dashboard",
            description="Build main dashboard layout and user management features",
            project_id=project4.id,
            status=SprintStatus.PLANNED,
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC) + timedelta(days=14),
            goal="Create functional admin dashboard",
            capacity_hours=140.0,
            velocity_points=22
        )

        db.session.add_all([sprint1, sprint2, sprint3, sprint4])
        db.session.commit()
        print("✅ Sprints created: 4")
    except Exception as e:
        print(f"❌ Error creating sprints: {e}")
        db.session.rollback()
        exit(1)

    # ===== TASKS =====
    try:
        print("📋 Creating tasks...")
        tasks = [
            # E-Commerce Platform Tasks (Sprint 1 - Completed)
            Task(
                title="Setup Project Repository and CI/CD",
                description="Initialize Git repository, setup GitHub Actions for CI/CD pipeline",
                status=TaskStatus.DONE,
                priority=TaskPriority.HIGH,
                task_type=TaskType.DEPLOYMENT,
                assigned_to_id=devops.id,
                created_by_id=manager.id,
                project_id=project1.id,
                sprint_id=sprint1.id,
                due_date=datetime.now(UTC) - timedelta(days=25),
                completion_date=datetime.now(UTC) - timedelta(days=24),
                estimated_hours=8.0,
                actual_hours=6.5,
                story_points=5
            ),
            
            Task(
                title="Database Schema Design and Implementation",
                description="Design and implement PostgreSQL database schema for e-commerce platform",
                status=TaskStatus.DONE,
                priority=TaskPriority.HIGH,
                task_type=TaskType.FEATURE,
                assigned_to_id=indal.id,
                created_by_id=manager.id,
                project_id=project1.id,
                sprint_id=sprint1.id,
                due_date=datetime.now(UTC) - timedelta(days=20),
                completion_date=datetime.now(UTC) - timedelta(days=19),
                estimated_hours=16.0,
                actual_hours=18.5,
                story_points=8,
                labels=json.dumps(["database", "backend", "critical"])
            ),

            Task(
                title="User Authentication System",
                description="Implement JWT-based authentication with registration, login, and password reset",
                status=TaskStatus.DONE,
                priority=TaskPriority.HIGH,
                task_type=TaskType.FEATURE,
                assigned_to_id=emp1.id,
                created_by_id=manager.id,
                project_id=project1.id,
                sprint_id=sprint1.id,
                due_date=datetime.now(UTC) - timedelta(days=18),
                completion_date=datetime.now(UTC) - timedelta(days=16),
                estimated_hours=20.0,
                actual_hours=22.0,
                story_points=8,
                acceptance_criteria="Users can register, login, logout, and reset passwords securely"
            ),

            # E-Commerce Platform Tasks (Sprint 2 - Active)
            Task(
                title="Product Catalog Management",
                description="Build product catalog with categories, search, and filtering functionality",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                task_type=TaskType.FEATURE,
                assigned_to_id=indal.id,
                created_by_id=manager.id,
                project_id=project1.id,
                sprint_id=sprint2.id,
                due_date=datetime.now(UTC) + timedelta(days=5),
                start_date=datetime.now(UTC) - timedelta(days=10),
                estimated_hours=32.0,
                actual_hours=20.0,
                story_points=13,
                labels=json.dumps(["product", "catalog", "search"])
            ),

            Task(
                title="Shopping Cart Implementation",
                description="Implement shopping cart functionality with add/remove/update quantities",
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                task_type=TaskType.FEATURE,
                assigned_to_id=emp1.id,
                created_by_id=manager.id,
                project_id=project1.id,
                sprint_id=sprint2.id,
                due_date=datetime.now(UTC) + timedelta(days=8),
                estimated_hours=24.0,
                story_points=8,
                acceptance_criteria="Users can add products to cart, modify quantities, and proceed to checkout"
            ),

            Task(
                title="UI/UX Design for Product Pages",
                description="Design responsive product listing and detail pages with modern UI",
                status=TaskStatus.IN_REVIEW,
                priority=TaskPriority.MEDIUM,
                task_type=TaskType.FEATURE,
                assigned_to_id=designer.id,
                created_by_id=manager.id,
                project_id=project1.id,
                sprint_id=sprint2.id,
                due_date=datetime.now(UTC) + timedelta(days=3),
                start_date=datetime.now(UTC) - timedelta(days=8),
                estimated_hours=16.0,
                actual_hours=14.0,
                story_points=5
            ),

            # Mobile App Tasks
            Task(
                title="React Native Project Setup",
                description="Initialize React Native project with navigation and basic components",
                status=TaskStatus.DONE,
                priority=TaskPriority.HIGH,
                task_type=TaskType.FEATURE,
                assigned_to_id=emp1.id,
                created_by_id=team_lead.id,
                project_id=project2.id,
                sprint_id=sprint3.id,
                due_date=datetime.now(UTC) - timedelta(days=10),
                completion_date=datetime.now(UTC) - timedelta(days=11),
                estimated_hours=12.0,
                actual_hours=10.0,
                story_points=5
            ),

            Task(
                title="Mobile App Authentication Flow",
                description="Implement login/register screens with biometric authentication support",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                task_type=TaskType.FEATURE,
                assigned_to_id=emp1.id,
                created_by_id=team_lead.id,
                project_id=project2.id,
                sprint_id=sprint3.id,
                due_date=datetime.now(UTC) + timedelta(days=5),
                start_date=datetime.now(UTC) - timedelta(days=5),
                estimated_hours=20.0,
                actual_hours=12.0,
                story_points=8
            ),

            # Bug and Maintenance Tasks
            Task(
                title="Fix Authentication Token Expiry Bug",
                description="Fix issue where JWT tokens expire too quickly causing frequent logouts",
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                task_type=TaskType.BUG,
                assigned_to_id=emp1.id,
                created_by_id=emp2.id,
                project_id=project1.id,
                due_date=datetime.now(UTC) + timedelta(days=2),
                estimated_hours=4.0,
                story_points=3,
                labels=json.dumps(["bug", "authentication", "urgent"])
            ),

            Task(
                title="Performance Optimization - Database Queries",
                description="Optimize slow database queries identified in performance testing",
                status=TaskStatus.BLOCKED,
                priority=TaskPriority.MEDIUM,
                task_type=TaskType.ENHANCEMENT,
                assigned_to_id=indal.id,
                created_by_id=team_lead.id,
                project_id=project1.id,
                due_date=datetime.now(UTC) + timedelta(days=7),
                estimated_hours=12.0,
                story_points=5,
                labels=json.dumps(["performance", "database", "optimization"])
            ),
        ]

        db.session.add_all(tasks)
        db.session.commit()
        
        # Get task IDs for further operations
        task_objects = db.session.query(Task).all()
        print(f"✅ Tasks created: {len(task_objects)}")
    except Exception as e:
        print(f"❌ Error creating tasks: {e}")
        db.session.rollback()
        exit(1)

    # ===== TASK COMMENTS =====
    try:
        print("💬 Creating task comments...")
        comments = []
        
        # Get some tasks for comments
        auth_task = db.session.query(Task).filter_by(title="User Authentication System").first()
        catalog_task = db.session.query(Task).filter_by(title="Product Catalog Management").first()
        mobile_auth_task = db.session.query(Task).filter_by(title="Mobile App Authentication Flow").first()
        bug_task = db.session.query(Task).filter_by(title="Fix Authentication Token Expiry Bug").first()

        if auth_task:
            comments.extend([
                TaskComment(task_id=auth_task.id, user_id=emp1.id, comment="Authentication system implemented with JWT. Added password strength validation and rate limiting for login attempts."),
                TaskComment(task_id=auth_task.id, user_id=manager.id, comment="Great work! Please ensure the password reset functionality is working correctly."),
                TaskComment(task_id=auth_task.id, user_id=emp2.id, comment="Tested the authentication flow - working perfectly. Ready for production deployment.")
            ])

        if catalog_task:
            comments.extend([
                TaskComment(task_id=catalog_task.id, user_id=indal.id, comment="Working on the search functionality. Implemented Elasticsearch integration for better search performance."),
                TaskComment(task_id=catalog_task.id, user_id=designer.id, comment="Product listing UI designs are ready. Shared the Figma prototypes in Slack."),
                TaskComment(task_id=catalog_task.id, user_id=manager.id, comment="Looking good! Please ensure mobile responsiveness is properly tested.")
            ])

        if mobile_auth_task:
            comments.extend([
                TaskComment(task_id=mobile_auth_task.id, user_id=emp1.id, comment="Biometric authentication integrated successfully. Testing on both iOS and Android devices."),
                TaskComment(task_id=mobile_auth_task.id, user_id=team_lead.id, comment="Excellent progress! Make sure to handle edge cases for devices without biometric support.")
            ])

        if bug_task:
            comments.extend([
                TaskComment(task_id=bug_task.id, user_id=emp2.id, comment="Bug reproduced consistently. Token expires after 15 minutes instead of configured 2 hours."),
                TaskComment(task_id=bug_task.id, user_id=emp1.id, comment="Found the issue in JWT configuration. Will fix and deploy today."),
                TaskComment(task_id=bug_task.id, user_id=manager.id, comment="High priority - this is affecting user experience significantly.")
            ])

        db.session.add_all(comments)
        db.session.commit()
        print(f"✅ Comments created: {len(comments)}")
    except Exception as e:
        print(f"❌ Error creating comments: {e}")
        db.session.rollback()
        exit(1)

    # ===== TIME LOGS =====
    try:
        print("⏰ Creating time logs...")
        time_logs = []
        
        # Add realistic time logs for completed and in-progress tasks
        completed_tasks = db.session.query(Task).filter_by(status=TaskStatus.DONE).all()
        in_progress_tasks = db.session.query(Task).filter_by(status=TaskStatus.IN_PROGRESS).all()
        
        for task in completed_tasks:
            if task.assigned_to_id and task.actual_hours:
                # Create multiple time log entries for completed tasks
                days_worked = random.randint(3, 8)
                hours_per_day = task.actual_hours / days_worked
                
                for i in range(days_worked):
                    log_date = task.completion_date - timedelta(days=days_worked-i-1) if task.completion_date else datetime.now(UTC).date()
                    daily_hours = round(hours_per_day + random.uniform(-1, 1), 1)
                    if daily_hours > 0:
                        time_logs.append(TimeLog(
                            task_id=task.id,
                            user_id=task.assigned_to_id,
                            hours=daily_hours,
                            description=f"Work on {task.title.lower()}",
                            work_date=log_date.date() if hasattr(log_date, 'date') else log_date
                        ))

        for task in in_progress_tasks:
            if task.assigned_to_id and task.actual_hours:
                # Create time logs for in-progress tasks
                days_worked = random.randint(2, 5)
                hours_per_day = task.actual_hours / days_worked
                
                for i in range(days_worked):
                    log_date = datetime.now(UTC) - timedelta(days=days_worked-i-1)
                    daily_hours = round(hours_per_day + random.uniform(-0.5, 0.5), 1)
                    if daily_hours > 0:
                        time_logs.append(TimeLog(
                            task_id=task.id,
                            user_id=task.assigned_to_id,
                            hours=daily_hours,
                            description=f"Progress on {task.title.lower()}",
                            work_date=log_date.date()
                        ))

        db.session.add_all(time_logs)
        db.session.commit()
        print(f"✅ Time logs created: {len(time_logs)}")
    except Exception as e:
        print(f"❌ Error creating time logs: {e}")
        db.session.rollback()
        exit(1)

    # ===== NOTIFICATIONS =====
    try:
        print("🔔 Creating notifications...")
        notifications = []
        
        # Get recent tasks for notifications
        recent_tasks = db.session.query(Task).limit(10).all()
        
        # Task assignment notifications
        for task in recent_tasks:
            if task.assigned_to_id:
                notifications.append(Notification(
                    user_id=task.assigned_to_id,
                    task_id=task.id,
                    type=NotificationType.TASK_ASSIGNED,
                    title="New Task Assigned",
                    message=f"You have been assigned: {task.title}",
                    related_user_id=task.created_by_id,
                    project_id=task.project_id,
                    read=random.choice([True, False])
                ))

        # Overdue task notifications
        overdue_tasks = db.session.query(Task).filter(
            Task.due_date < datetime.now(UTC),
            Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED])
        ).all()
        
        for task in overdue_tasks:
            if task.assigned_to_id:
                notifications.append(Notification(
                    user_id=task.assigned_to_id,
                    task_id=task.id,
                    type=NotificationType.TASK_OVERDUE,
                    title="Task Overdue",
                    message=f"Task overdue: {task.title} - Please update status",
                    project_id=task.project_id,
                    read=False
                ))
                
                # Also notify project manager
                if task.project and task.project.owner_id:
                    notifications.append(Notification(
                        user_id=task.project.owner_id,
                        task_id=task.id,
                        type=NotificationType.TASK_OVERDUE,
                        title="Team Task Overdue",
                        message=f"Team task overdue: {task.title} (Assigned to {task.assignee.name if task.assignee else 'Unknown'})",
                        related_user_id=task.assigned_to_id,
                        project_id=task.project_id,
                        read=False
                    ))

        # Task completion notifications
        completed_tasks = db.session.query(Task).filter_by(status=TaskStatus.DONE).limit(5).all()
        for task in completed_tasks:
            if task.created_by_id and task.created_by_id != task.assigned_to_id:
                notifications.append(Notification(
                    user_id=task.created_by_id,
                    task_id=task.id,
                    type=NotificationType.TASK_COMPLETED,
                    title="Task Completed",
                    message=f"Task completed: {task.title}",
                    related_user_id=task.assigned_to_id,
                    project_id=task.project_id,
                    read=random.choice([True, False])
                ))

        # Comment notifications
        recent_comments = db.session.query(TaskComment).limit(10).all()
        
        for comment in recent_comments:
            if comment.task and comment.task.assigned_to_id and comment.task.assigned_to_id != comment.user_id:
                notifications.append(Notification(
                    user_id=comment.task.assigned_to_id,
                    task_id=comment.task_id,
                    type=NotificationType.COMMENT_ADDED,
                    title="New Comment",
                    message=f"New comment on task: {comment.task.title}",
                    related_user_id=comment.user_id,
                    project_id=comment.task.project_id,
                    read=random.choice([True, False])
                ))

        # Project update notifications
        for project in [project1, project2, project4]:
            team_members = db.session.query(ProjectMember).filter_by(project_id=project.id).all()
            for member in team_members:
                notifications.append(Notification(
                    user_id=member.user_id,
                    project_id=project.id,
                    type=NotificationType.PROJECT_UPDATED,
                    title="Project Update",
                    message=f"Project updated: {project.name}",
                    related_user_id=project.owner_id,
                    read=random.choice([True, False])
                ))

        # Sprint notifications
        for sprint in [sprint2, sprint3]:
            if sprint.project:
                team_members = db.session.query(ProjectMember).filter_by(project_id=sprint.project_id).all()
                for member in team_members:
                    notifications.append(Notification(
                        user_id=member.user_id,
                        sprint_id=sprint.id,
                        project_id=sprint.project_id,
                        type=NotificationType.SPRINT_STARTED,
                        title="Sprint Started",
                        message=f"Sprint started: {sprint.name}",
                        related_user_id=sprint.project.owner_id,
                        read=random.choice([True, False])
                    ))

        # Personal notifications for Indal
        indal_notifications = [
            Notification(
                user_id=indal.id,
                type=NotificationType.MENTION,
                title="You were mentioned",
                message="You were mentioned in a discussion about database optimization",
                related_user_id=team_lead.id,
                read=False
            ),
            Notification(
                user_id=indal.id,
                type=NotificationType.TASK_UPDATED,
                title="Task Priority Updated",
                message="Task priority has been updated to HIGH for performance optimization task",
                related_user_id=manager.id,
                read=False
            )
        ]
        notifications.extend(indal_notifications)

        db.session.add_all(notifications)
        db.session.commit()
        print(f"✅ Notifications created: {len(notifications)}")
    except Exception as e:
        print(f"❌ Error creating notifications: {e}")
        db.session.rollback()
        exit(1)

    # ===== SUMMARY =====
    print("\n" + "="*60)
    print("🎉 COMPREHENSIVE DATA IMPORT COMPLETED SUCCESSFULLY!")
    print("="*60)
    
    # Get actual counts from database
    user_count = db.session.query(User).count()
    project_count = db.session.query(Project).count()
    task_count = db.session.query(Task).count()
    comment_count = db.session.query(TaskComment).count()
    notification_count = db.session.query(Notification).count()
    sprint_count = db.session.query(Sprint).count()
    member_count = db.session.query(ProjectMember).count()
    timelog_count = db.session.query(TimeLog).count()
    
    print(f"👥 Users created: {user_count}")
    print(f"📁 Projects created: {project_count}")
    print(f"🏃 Sprints created: {sprint_count}")
    print(f"📋 Tasks created: {task_count}")
    print(f"💬 Comments created: {comment_count}")
    print(f"🔔 Notifications created: {notification_count}")
    print(f"👥 Project members: {member_count}")
    print(f"⏰ Time logs created: {timelog_count}")

    print("\n" + "="*60)
    print("🔐 LOGIN CREDENTIALS")
    print("="*60)
    print("👑 Admin             : admin@example.com / admin123")
    print("👨‍💼 Project Manager  : manager@example.com / manager123")
    print("👨‍💻 Team Lead        : teamlead@example.com / lead123")
    print("🧑‍💻 You (Indal)      : indalsaroj404@gmail.com / 123456789")
    print("👨‍💻 John Doe         : john@example.com / john123")
    print("👩‍💻 Jane Smith       : jane@example.com / jane123")
    print("🎨 Emily Rodriguez   : emily@example.com / emily123")
    print("⚙️  Alex Thompson    : alex@example.com / alex123")
    print("📊 Lisa Wang         : lisa@example.com / lisa123")
    
    print("\n" + "="*60)
    print("📊 DATA BREAKDOWN")
    print("="*60)
    print("Projects by Status:")
    for status in ProjectStatus:
        count = db.session.query(Project).filter_by(status=status).count()
        if count > 0:
            print(f"  • {status.value}: {count}")
    
    print("\nTasks by Status:")
    for status in TaskStatus:
        count = db.session.query(Task).filter_by(status=status).count()
        if count > 0:
            print(f"  • {status.value}: {count}")
    
    print("\nTasks by Priority:")
    for priority in TaskPriority:
        count = db.session.query(Task).filter_by(priority=priority).count()
        if count > 0:
            print(f"  • {priority.value}: {count}")

    # Show user workloads
    print("\n👥 User Workloads (Active Tasks):")
    for user in [indal, emp1, emp2, designer, devops]:
        active_tasks = db.session.query(Task).filter(
            Task.assigned_to_id == user.id,
            Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED])
        ).count()
        print(f"  • {user.name}: {active_tasks} active tasks")

    print("\n" + "="*60)
    print("✨ Your Task Management System is ready for comprehensive testing!")
    print("🚀 Features included:")
    print("   • Multiple user roles and realistic profiles")
    print("   • Complex project structures with team members")
    print("   • Sprint management with active/completed sprints")
    print("   • Diverse task types (features, bugs, enhancements)")
    print("   • Time tracking with realistic work logs")
    print("   • Rich notification system")
    print("   • Task comments and collaboration")
    print("   • Overdue tasks and priority management")
    print("="*60)
    print("✨ Ready to test your Task Management System!")