import random
import os
from datetime import datetime, date, timedelta
from collections import defaultdict
from config import *



from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_roles_and_permissions = create_roles_and_permissions
SQLDataGenerator.create_roles_and_permissions = create_roles_and_permissions