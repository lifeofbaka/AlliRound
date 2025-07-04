# Generated by Django 5.0.6 on 2024-10-12 05:36

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flights", "0004_flightsearchcache_alter_flight_search_date_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="flight",
            name="search_date",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2024, 10, 12, 5, 36, 34, 249356, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="flightsearchbreakdown",
            name="search_date",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2024, 10, 12, 5, 36, 34, 280674, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="flightsearchcache",
            name="search_date",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2024, 10, 12, 5, 36, 34, 281099, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
