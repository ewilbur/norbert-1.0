import discord
import itertools
from discord.ext import commands
from discord.utils import get
from discord.ext.commands import has_permissions
import os
from dotenv import load_dotenv

load_dotenv()

classroom_prefix = 'class'
student_prefix = 'student'

class Course:
    __courseRole    = discord.Role
    __courseName    = 'error'
    __courseChannels = [] 

    def __init__(self, courseRole, courseName, *args):
        self.__courseRole = courseRole
        self.__courseName = courseName
        self.__courseChannels = list(args)
    
    def courseRole(self):
        return self.__courseRole

    def courseName(self):
        return self.__courseName

    def courseChannel(self):
        return self._courseChannel

    def setCourseName(self, courseName):
        self.__courseName = courseName

    def setCourseRole(self, courseRole):
        self.__courseRole = courseRole

    def setCourseChannels(self, courseChannel):
        self.__courseChannels = courseChannel

    def setCourseClassrooms(self, courseClassrooms):
        self.__courseChannels = courseClassrooms

    @staticmethod
    def courseNameValid(courseName):
        return courseName.isalnum() and len(courseName) <= 8 and courseName[-4:].isnumeric() and courseName[:-4].isalpha()

    @classmethod
    def fromCourseName(cls, courseName):
        if Course.courseNameValid(courseName):
            return cls(discord.Role, courseName, discord.TextChannel)
        else:
            raise Exception('error: Invalid course name format. Must be a 3-4 letters followed by 4 digits.')

bot = commands.Bot(command_prefix='!')

def get_courses(ctx):
    return filter(lambda role: role.name.startswith(student_prefix), ctx.guild.roles)

def get_classrooms(ctx):
    return filter(lambda chnl: chnl.name.startswith(classroom_prefix), ctx.guild.channels)

def get_course_classrooms(ctx, courseName):
    return filter(lambda chnl: chnl.name.startswith('-'.join([classroom_prefix, courseName])), ctx.guild.channels)

def get_course(ctx, course):
    for crs in get_courses(ctx):
        if crs.name.split('-')[1] == course:
            return crs
    return None

async def create_student_role(ctx, course):
    course_role = get_course(ctx, course)
    if course_role == None:
        role = await ctx.guild.create_role(name = '-'.join([student_prefix, course]), permissions = discord.Permissions.none(), reason = 'Create a student role for class')
        return role
    else:
        return course_role

async def create_student_classroom(ctx, course):
    classrooms = list(get_course_classrooms(ctx, course))
    if not classrooms:
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages = False)
        }
        clsrm = await ctx.guild.create_text_channel(name = '-'.join([classroom_prefix, course]), overwrites = overwrites)
        return clsrm
    else:
        return classrooms[0]
    
async def join_single_class(ctx, course):
    if not Course.courseNameValid(course):
        await ctx.reply(f'error: invalid course name ({course})')
        return
    clsrm = await create_student_classroom(ctx, course)
    clsrl = await create_student_role(ctx, course)
    await clsrm.set_permissions(clsrl, read_messages = True, send_messages = True, send_tts_messages = True, read_message_history = True, attach_files = True, manage_messages = True, embed_links = True)
    await ctx.author.add_roles(clsrl)
    await ctx.reply(f'{ctx.author.name} has been added to {course}')

async def drop_single_class(ctx, course):
    if not Course.courseNameValid(course):
        await ctx.reply(f'error: invalid course name ({course})')
        return
    clsrl = discord.utils.get(ctx.author.roles, name = '-'.join([student_prefix, course]))
    if clsrl:
        await ctx.author.remove_roles(clsrl, reason = f'{ctx.author.name} asked to be removed from {course}')
        await ctx.reply(f'{ctx.author.name} has been removed from {course}')
    else:
        await ctx.reply(f'{ctx.author.name} is not enrolled in {course}')

async def purge_single_class(ctx, course):
    if not Course.courseNameValid(course):
        await ctx.reply(f'error: invalid course name ({course})')
        return

    clsrl = discord.utils.get(ctx.guild.roles, name = '-'.join([student_prefix, course]))
    clsrm = discord.utils.get(ctx.guild.channels, name = '-'.join([classroom_prefix, course]))
    
    if clsrl:
        await clsrl.delete()
    if clsrm:
        await clsrm.delete()
    await ctx.reply(f'Removed {course}')

@bot.command()
@has_permissions(manage_channels = True, manage_roles = True)
async def purgeclass(ctx, *args):
    for cls in args:
        await purge_single_class(ctx, cls)

@bot.command()
async def dropclass(ctx, *args):
    if ctx.channel.name != 'manage-classes':
        return
    for cls in args:
        await drop_single_class(ctx, cls)

@bot.command()
async def joinclass(ctx, *args):
    if ctx.channel.name != 'manage-classes':
        return
    for cls in args:
        await join_single_class(ctx, cls)

@bot.command()
async def enrolledclass(ctx): 
    if ctx.channel.name != 'manage-classes':
        return 
    user_classes = filter(lambda role: role.name.startswith(student_prefix), ctx.author.roles)
    resp = []
    for cls in user_classes:
        resp.append(cls.name.split('-')[1])
    if len(resp) == 0:
        await ctx.reply(f'{ctx.author.name} is not enrolled in any classes')
    else:
        await ctx.reply('\n'.join(resp))

@bot.command()
async def listclass(ctx):
    if ctx.channel.name != 'manage-classes':
        return
    courses = get_courses(ctx)
    resp = []
    for course in courses:
        resp.append(course.name.split('-')[1])

    if len(resp) == 0:
        await ctx.reply('No classes are available!')
    else:
        try:
            await ctx.reply(content = '\n'.join(resp))
        except discord.HTTPException as err:
            print('error: unable to make connection to server.', str(err))
        except Forbidden as err:
            print('error: incorrect permissions.', str(err))
        except err:
            print('error:', str(err))

bot.run(os.getenv('DISCORD_TOKEN'))
