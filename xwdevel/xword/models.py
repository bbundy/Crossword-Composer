from django.db import models

class Clue(models.Model):
    setter = models.ForeignKey('User')
    puzzle = models.ForeignKey('Puzzle')
    type = models.ForeignKey('PuzzleType')
    answer = models.CharField(max_length=255, db_index=True)
    rebus = models.CharField(max_length=30)
    num = models.IntegerField()
    row = models.IntegerField()
    col = models.IntegerField()
    dir = models.IntegerField()
    text = models.CharField(max_length=255)

class Answer(models.Model):
    answer = models.CharField(max_length=255, unique=True, db_index=True)
    count = models.IntegerField()

class Pattern(models.Model):
    pattern = models.CharField(max_length=255, unique=True, db_index=True)
    count = models.IntegerField()

class Grid(models.Model):
    format = models.CharField(max_length=255, unique=True)
    type = models.ForeignKey('PuzzleType')

class Puzzle(models.Model):
    setter = models.ForeignKey('User', related_name="puzzle_setter")
    editor = models.ForeignKey('User', related_name="puzzle_editor")
    publisher = models.ForeignKey('User', related_name="puzzle_publisher")
    grid = models.ForeignKey('Grid')
    type = models.ForeignKey('PuzzleType')
    date = models.DateField()
    title = models.CharField(max_length=255)
    permission_list = models.CharField(max_length=255)
        
class PuzzleType(models.Model):
    type = models.CharField(max_length=255)

class UserType(models.Model):
    type = models.CharField(max_length=255)

class User(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(max_length=50)
    joined = models.DateField()
    puzzle_pref = models.ForeignKey('PuzzleType')
    user_type = models.ForeignKey('UserType')
    username = models.CharField(max_length=30, unique=True, db_index=True)
    password = models.CharField(max_length=255)

class RawPuzzles(models.Model):
    author_title = models.CharField(max_length=255, unique=True, db_index=True)
    created = models.DateTimeField(auto_now=True)
    modified = models.DateTimeField(auto_now_add=True)
    contents=models.CharField(max_length=32000)

class SolvePuzzles(models.Model):
    author_title = models.CharField(max_length=255, unique=True, db_index=True)
    created = models.DateTimeField(auto_now=True)
    modified = models.DateTimeField(auto_now_add=True)
    contents=models.CharField(max_length=32000)
