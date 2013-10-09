# Dependencies

see requirements.txt
memcached daemon must be running on server
OR if it's not then comment out the cache_backend line in settings.py

see also the doc/ directory

# Apps:

# search

this is the api that does all the querying of the database for searching

# metadata

information about the data, range endpoints, nulls, total result counts, etc

# paraminfo

information about every searchable parameter (type, default widget, how to query etc..)

# results

handles returning results

# ui

drives the OPUS user interface

# guide

a guide for using the API for querying opus from script or command line



# some instructs on other stuff:

========  Creating Grouped Widgets ========

Some multi-checkbox widgets have too many options, so you want to group them
to trigger grouping for a widget do this:

1.  add a field called 'grouping' to the mult table you want to be grouped

    update the grouping field with your data,

    for example, there are too many target names, so we group them by planet
    so the table mult_target_name we added a field called 'grouping' which holds the planet_id value

     grouping = models.CharField(max_length=7)


    if your groups are described by another mult_table (in this case in mult_planet_id) make
    sure you update the grouping field with mult_planet_id.value (rather than the mult_planet_id.label)

2.  add a model class to metadata.models.py

	Name it like; GroupingModelName

    the model should have the same structure as other mult_ tables (minus the "grouping" field)

    this model essentially tells opus the display order of the groups and what labels to display
    if your groups should be identical to those found in another mult_table then create the model
    and then in the database manually create a View table for that mult_table, this assures
    the data in your grouping model stays up to date.

	For the planet/target example, this new model is called GroupingTargetName
	and so we created a model in metadata.models.py called GroupingTargetName,
	We want to group them by valid planet labels, so we have a mult_table already for that: mult_planet_id
    the model body is copied/pasted from the MultTargetName model in search.models.py
    and to make sure the data stays current, the table was created like so:

		create view grouping_target_name as select * from mult_planet_id;

3. update the janky migration script
	• add the above 'create view' statement to the OPUS1 to OPUS2 migration script under "grouped widgets" in build_obs.py
    • add the model declaration in #1 to the model, ie:
		grouping = models.CharField(max_length=7)


That's all.
This will trigger ui.models.getWidget and search.forms.searchForm to create a grouped wiget
Note the widget ui display will default to all groups being closed. If you want one default open or other
behaviors you must code that in the javascript, see method customWidgetBehaviors.

