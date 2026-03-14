# app/models/user.py
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .enums import UserRole

# Import logging and caching utilities
from app.utils.logger import get_logger, log_auth_event, log_db_query
from app.utils.cache_utils import cache, cached_per_user, invalidate_user_cache, CacheKeys

# Initialize logger for this module
logger = get_logger('users')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    
    # Profile information
    avatar_url = db.Column(db.String(500))
    bio = db.Column(db.Text)
    skills = db.Column(db.Text)  # JSON string of skills
    github_username = db.Column(db.String(100))
    linkedin_url = db.Column(db.String(500))
    phone = db.Column(db.String(20))
    timezone = db.Column(db.String(50), default='UTC')
    
    # Work preferences
    daily_work_hours = db.Column(db.Float, default=8.0)
    hourly_rate = db.Column(db.Float)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Task relationships
    created_tasks = db.relationship('Task', foreign_keys='Task.created_by_id', back_populates='creator', cascade='all, delete-orphan')
    assigned_tasks = db.relationship('Task', foreign_keys='Task.assigned_to_id', back_populates='assignee')

    # Project relationships
    owned_projects = db.relationship('Project', back_populates='owner', cascade='all, delete-orphan')
    project_memberships = db.relationship('ProjectMember', back_populates='user', cascade='all, delete-orphan')
    
    # Other relationships
    notifications = db.relationship('Notification', back_populates='user', foreign_keys='Notification.user_id')
    task_comments = db.relationship('TaskComment', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        """Set user password with logging."""
        logger.debug(f"Setting password for user {self.id}")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check user password with logging."""
        result = check_password_hash(self.password_hash, password)
        logger.debug(f"Password check for user {self.email}: {'SUCCESS' if result else 'FAILED'}")
        return result

    @classmethod
    def register(cls, name, email, password, role):
        """Register new user with comprehensive logging and cache management."""
        logger.info(f"Attempting to register user with email: {email}")
        
        # Check if email already exists
        if cls.query.filter_by(email=email).first():
            logger.warning(f"Registration failed: Email {email} already registered")
            raise ValueError("Email already registered")
        
        # Create new user
        user = cls(name=name, email=email, role=role)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Log successful registration
            log_auth_event("REGISTER", user.id, email, True)
            logger.info(f"User registered successfully: {user.id} - {email}")
            
            # Clear user list cache since we added a new user
            cache.delete('all_users_list')
            
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration failed for {email}: {str(e)}")
            log_auth_event("REGISTER", None, email, False)
            raise

    @classmethod
    def login(cls, email, password):
        """User login with enhanced logging and cache updates."""
        logger.info(f"Login attempt for email: {email}")
        
        try:
            user = cls.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                # Update last login time
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Log successful login
                log_auth_event("LOGIN", user.id, email, True)
                logger.info(f"Login successful for user {user.id}")
                
                # Invalidate user cache to refresh with new last_login
                invalidate_user_cache(user.id)
                
                return user
            else:
                # Log failed login
                log_auth_event("LOGIN", None, email, False)
                logger.warning(f"Login failed for email: {email}")
                return None
                
        except Exception as e:
            logger.error(f"Login error for {email}: {str(e)}")
            return None

    def update_profile(self, name=None, email=None, bio=None, skills=None, 
                      github_username=None, linkedin_url=None, phone=None, 
                      timezone=None, daily_work_hours=None, hourly_rate=None):
        """Update user profile with logging and cache invalidation."""
        logger.info(f"Updating profile for user {self.id}")
        
        # Check email uniqueness
        if email and User.query.filter(User.email == email, User.id != self.id).first():
            logger.warning(f"Profile update failed: Email {email} already in use")
            raise ValueError("Email already in use by another user")
        
        # Track changes for logging
        changes = []
        
        if name and name != self.name:
            changes.append(f"name: {self.name} -> {name}")
            self.name = name
        if email and email != self.email:
            changes.append(f"email: {self.email} -> {email}")
            self.email = email
        if bio is not None and bio != self.bio:
            changes.append("bio updated")
            self.bio = bio
        if skills is not None and skills != self.skills:
            changes.append("skills updated")
            self.skills = skills
        if github_username is not None and github_username != self.github_username:
            changes.append(f"github: {github_username}")
            self.github_username = github_username
        if linkedin_url is not None and linkedin_url != self.linkedin_url:
            changes.append("linkedin updated")
            self.linkedin_url = linkedin_url
        if phone is not None and phone != self.phone:
            changes.append("phone updated")
            self.phone = phone
        if timezone is not None and timezone != self.timezone:
            changes.append(f"timezone: {timezone}")
            self.timezone = timezone
        if daily_work_hours is not None and daily_work_hours != self.daily_work_hours:
            changes.append(f"work_hours: {daily_work_hours}")
            self.daily_work_hours = daily_work_hours
        if hourly_rate is not None and hourly_rate != self.hourly_rate:
            changes.append("hourly_rate updated")
            self.hourly_rate = hourly_rate
        
        if changes:
            try:
                db.session.commit()
                logger.info(f"Profile updated for user {self.id}: {', '.join(changes)}")
                
                # Invalidate user-related caches
                invalidate_user_cache(self.id)
                cache.delete('all_users_list')  # Clear user list cache
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Profile update failed for user {self.id}: {str(e)}")
                raise
        else:
            logger.debug(f"No changes in profile update for user {self.id}")

    def assign_task(self, task):
        """Assign task to user with logging."""
        if task.assigned_to_id is not None:
            logger.warning(f"Task {task.id} assignment failed: already assigned to user {task.assigned_to_id}")
            raise ValueError("Task is already assigned to someone else.")
        
        task.assigned_to_id = self.id
        db.session.commit()
        
        logger.info(f"Task {task.id} assigned to user {self.id}")
        
        # Invalidate user's task cache
        invalidate_user_cache(self.id, CacheKeys.USER_TASKS)

    @cached_per_user(timeout=300, key_prefix=CacheKeys.USER_TASKS)
    def get_tasks(self):
        """Get user's assigned tasks with caching."""
        logger.debug(f"Fetching tasks for user {self.id}")
        return self.assigned_tasks

    @cached_per_user(timeout=600, key_prefix=CacheKeys.USER_PROJECTS)
    def get_projects(self):
        """Get all projects user is involved in (owned or member) with caching."""
        logger.debug(f"Fetching projects for user {self.id}")
        owned = self.owned_projects
        member_projects = [membership.project for membership in self.project_memberships]
        return list(set(owned + member_projects))

    def get_project_role(self, project_id):
        """Get user's role in a specific project."""
        membership = next((m for m in self.project_memberships if m.project_id == project_id), None)
        return membership.role if membership else None

    def has_project_permission(self, project_id, permission):
        """Check if user has specific permission in a project."""
        # Project owner has all permissions
        if any(p.id == project_id for p in self.owned_projects):
            return True
        
        # Check project membership permissions
        membership = next((m for m in self.project_memberships if m.project_id == project_id), None)
        return membership.has_permission(permission) if membership else False

    @cached_per_user(timeout=300, key_prefix="user_workload")
    def get_workload(self):
        """Calculate user's current workload with caching."""
        logger.debug(f"Calculating workload for user {self.id}")
        
        active_tasks = [task for task in self.assigned_tasks 
                       if task.status.value not in ['DONE', 'CANCELLED']]
        
        total_hours = sum(task.estimated_hours or 0 for task in active_tasks)
        workload_data = {
            'active_tasks_count': len(active_tasks),
            'estimated_hours': total_hours,
            'workload_percentage': min((total_hours / (self.daily_work_hours * 5)) * 100, 100) if self.daily_work_hours else 0
        }
        
        logger.debug(f"User {self.id} workload: {workload_data['workload_percentage']:.1f}%")
        return workload_data

    def add_skill(self, skill):
        """Add a skill to user's profile with logging."""
        import json
        skills = []
        if self.skills:
            try:
                skills = json.loads(self.skills)
            except json.JSONDecodeError:
                skills = []
        
        if skill not in skills:
            skills.append(skill)
            self.skills = json.dumps(skills)
            db.session.commit()
            
            logger.info(f"Added skill '{skill}' to user {self.id}")
            invalidate_user_cache(self.id)

    def remove_skill(self, skill):
        """Remove a skill from user's profile with logging."""
        import json
        skills = []
        if self.skills:
            try:
                skills = json.loads(self.skills)
            except json.JSONDecodeError:
                return
        
        if skill in skills:
            skills.remove(skill)
            self.skills = json.dumps(skills)
            db.session.commit()
            
            logger.info(f"Removed skill '{skill}' from user {self.id}")
            invalidate_user_cache(self.id)

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary with caching consideration."""
        import json
        
        # Parse skills from JSON string
        skills_list = []
        if self.skills:
            try:
                skills_list = json.loads(self.skills)
            except json.JSONDecodeError:
                skills_list = []

        result = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role.value,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'skills': skills_list,
            'github_username': self.github_username,
            'linkedin_url': self.linkedin_url,
            'timezone': self.timezone,
            'daily_work_hours': self.daily_work_hours,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_sensitive:
            result.update({
                'phone': self.phone,
                'hourly_rate': self.hourly_rate
            })
            
        return result

    @classmethod
    @cache.cached(timeout=300, key_prefix='all_users_list')
    def get_all_user_ids_and_names(cls):
        """Get all active users with caching."""
        logger.debug("Fetching all active users list")
        users = cls.query.filter_by(is_active=True).all()
        return [{"id": user.id, "name": user.name, "role": user.role.value} for user in users]

    def deactivate(self):
        """Deactivate user account with logging and cache cleanup."""
        logger.info(f"Deactivating user {self.id}")
        self.is_active = False
        db.session.commit()
        
        # Clear related caches
        invalidate_user_cache(self.id)
        cache.delete('all_users_list')

    def activate(self):
        """Activate user account with logging and cache cleanup."""
        logger.info(f"Activating user {self.id}")
        self.is_active = True
        db.session.commit()
        
        # Clear related caches
        invalidate_user_cache(self.id)
        cache.delete('all_users_list')