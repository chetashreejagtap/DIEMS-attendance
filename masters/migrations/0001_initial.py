# Generated by Django 4.2.4 on 2023-09-26 08:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('short', models.CharField(max_length=20, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=100, null=True)),
                ('academic_year', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='PracticalBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_name', models.CharField(max_length=50)),
                ('student_class', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='masters.class')),
            ],
        ),
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sem_year', models.PositiveSmallIntegerField(choices=[(1, 'FY'), (2, 'SY'), (3, 'TY'), (4, 'Final Yr')])),
                ('sem_num', models.IntegerField()),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.department')),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('subject_id', models.AutoField(primary_key=True, serialize=False)),
                ('subject_name', models.CharField(max_length=50)),
                ('subject_type', models.PositiveSmallIntegerField(choices=[(1, 'Theory'), (2, 'Practical'), (3, 'Elective'), (4, 'Other_Session')])),
                ('subject_code', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('description', models.TextField()),
                ('att_score', models.IntegerField(default=1)),
                ('sem', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='masters.semester')),
            ],
        ),
        migrations.CreateModel(
            name='TheoryElective',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('elective_name', models.CharField(max_length=50)),
                ('student_class', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='masters.class')),
            ],
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thumb_id', models.CharField(max_length=10, unique=True)),
                ('first_name', models.CharField(max_length=50)),
                ('middle_name', models.CharField(blank=True, max_length=50, null=True)),
                ('last_name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.department')),
            ],
        ),
        migrations.CreateModel(
            name='SubjectAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_lectures', models.IntegerField(default=0)),
                ('sel_batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.practicalbatch')),
                ('sel_class', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.class')),
                ('sel_elective', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.theoryelective')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.subject')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.teacher')),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batu_prn', models.CharField(max_length=20, unique=True)),
                ('prn', models.CharField(max_length=10, unique=True)),
                ('roll_no', models.IntegerField(default=0)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('self_phone_number', models.CharField(max_length=15)),
                ('parents_phone_number', models.CharField(max_length=15)),
                ('first_name', models.CharField(max_length=50)),
                ('middle_name', models.CharField(blank=True, max_length=50, null=True)),
                ('last_name', models.CharField(max_length=50)),
                ('address', models.TextField()),
                ('batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='masters.practicalbatch')),
                ('department', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='masters.department')),
                ('elective', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='masters.theoryelective')),
                ('sem', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='masters.semester')),
                ('student_class', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='masters.class')),
            ],
        ),
        migrations.CreateModel(
            name='LectureTaken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lecture_date', models.DateField()),
                ('time_slot', models.TimeField()),
                ('batch_field', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.practicalbatch')),
                ('class_field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.class')),
                ('elective_field', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.theoryelective')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.subject')),
                ('took_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.teacher')),
            ],
        ),
        migrations.AddField(
            model_name='department',
            name='head_of_department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='department_head', to='masters.teacher'),
        ),
        migrations.AddField(
            model_name='class',
            name='classTeacher',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='masters.teacher'),
        ),
        migrations.AddField(
            model_name='class',
            name='sem',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.SET_DEFAULT, to='masters.semester'),
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_present', models.BooleanField(default=False)),
                ('remark', models.CharField(blank=True, max_length=200, null=True)),
                ('student', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.student')),
                ('subject', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.lecturetaken')),
            ],
        ),
    ]
