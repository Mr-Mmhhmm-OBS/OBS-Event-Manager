obs=obslua
days_of_week = { "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday" }

weekday = 0
time = 42

start_scene = ""

preshow_triggered = false
preshow_duration = 300

countdown_triggered = false
countdown_duration = 60
countdown_offset = 10

auto_start_streaming = true

auto_start_time_type = { "--Disabled--", "Preshow", "Countdown" }
auto_start_recording = 3

function set_countdown_text()
	print("update countdown")
	if after_time(time, countdown_offset) then
		print("live soon")
		obs.remove_current_callback()
	end
end

function after_time(start_time, offset)
	start_time = start_time - (offset / 3600 * 4)
	start_time = os.time{
		year=os.date("%Y"), 
		month=os.date("%m"), 
		day=os.date("%d"), 
		hour=math.floor(start_time / 4), 
		min= ((start_time % 4) * 15) % 60,
		sec=(((start_time % 4) * 15) / 60) % 60
	}
	return os.difftime(start_time, os.time()) < 0
end

function current_scene_name()
	local scene = obs.obs_frontend_get_current_scene()
	local scene_name = obs.obs_source_get_name(scene)
	obs.obs_source_release(scene);
	return scene_name
end

function check_start()
	if after_time(time, preshow_duration) and not preshow_triggered then
		print('preshow')
		preshow_triggered = true
		if current_scene_name() ~= start_scene then
			local scenes = obs.obs_frontend_get_scenes()
			if scenes ~= nil then
				for _, scene in ipairs(scenes) do
					scene_name = obs.obs_source_get_name(scene);
					if scene_name == start_scene then
						obs.obs_frontend_set_current_scene(scene)
						break
					end
				end
			end
			obs.source_list_release(scenes)
		end

		if auto_start_streaming and not obs.obs_frontend_streaming_active() then
			print('start stream')
			obs.obs_frontend_streaming_start()
		end

		if auto_start_recording == 2 and not obs.obs_frontend_recording_active() then
			obs.obs_frontend_recording_start()
		end
	end

	if after_time(time, countdown_duration + countdown_offset) and not countdown_triggered then
		print("countdown")
		countdown_triggered = true

		obs.timer_add(set_countdown_text, 1000)

		if auto_start_recording == 3 and not obs.obs_frontend_recording_active() then
			obs.obs_frontend_recording_start()
		end
		obs.remove_current_callback()
	end
end

function on_event(event)
	if event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING and weekday == os.date("%w") and not after_time(time, 0) then
		obs.timer_add(check_start, 1000)
	end
end

function script_load(settings)
	obs.obs_frontend_add_event_callback(on_event)
end

function script_description()
	return "Automatically starts the event at the pre-selected time.\n\nMade by Andrew Carbert"
end

function script_properties()
	local props = obs.obs_properties_create()
	
	local datetime_group = obs.obs_properties_create()
	local prop = obs.obs_properties_add_list(datetime_group, "weekday", "Day of Week", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
	for i in pairs(days_of_week) do
		obs.obs_property_list_add_int(prop, days_of_week[i], i - 1)
	end
		
	prop = obs.obs_properties_add_list(datetime_group, "time", "Time", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
	for i=0,24*4-1 do
		obs.obs_property_list_add_int(prop, string.format("%02d:%02d", math.floor(i/4), (i%4) * 15), i)
	end
	obs.obs_properties_add_group(props, "datetime_group", "Event Start", obs.OBS_GROUP_NORMAL, datetime_group)

	local start_scene_list = obs.obs_properties_add_list(props, "start_scene", "Start Scene", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	local scene_names = obs.obs_frontend_get_scene_names()
	if scene_names ~= nil then
		for _, scene_name in ipairs(scene_names) do
			obs.obs_property_list_add_string(start_scene_list, scene_name, scene_name)
		end
	end

	obs.obs_properties_add_int_slider(props, "preshow_duration", "Pre-Show Duration", 60, 300, 15)

	local countdown_text_list = obs.obs_properties_add_list(props, "countdown_text", "Countdown Text", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	local sources = obs.obs_enum_sources()
	if sources ~= nil then
		for _, source in ipairs(sources) do
			source_id = obs.obs_source_get_unversioned_id(source)
			if source_id == "text_gdiplus" or source_id == "text_ft2_source" then
				local name = obs.obs_source_get_name(source)
				obs.obs_property_list_add_string(countdown_text_list, name, name)
			end
		end
	end
	obs.source_list_release(sources)

	obs.obs_properties_add_int_slider(props, "countdown_duration", "Countdown Duration", 10, 300, 5)
	obs.obs_properties_add_int_slider(props, "countdown_offset", "Countdown Offset", -300, 300, 10)

	obs.obs_properties_add_bool(props, "auto_start_streaming", "Auto Start Streaming")

	local start_recording_list = obs.obs_properties_add_list(props, "auto_start_recording", "Start Recording", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
	for key, value in ipairs(auto_start_time_type) do
		obs.obs_property_list_add_int(start_recording_list, value, key)
	end

	return props
end

function script_defaults(settings)
	obs.obs_data_set_default_int(settings, "weekday", weekday)
	obs.obs_data_set_default_int(settings, "time", time)

	obs.obs_data_set_default_int(settings, "preshow_duration", preshow_duration)
	obs.obs_data_set_default_int(settings, "countdown_duration", countdown_duration)
	obs.obs_data_set_default_int(settings, "countdown_offset", countdown_offset)

	obs.obs_data_set_default_bool(settings, "auto_start_streaming", auto_start_streaming)

	obs.obs_data_set_default_int(settings, "auto_start_recording", auto_start_recording)
end

function script_update(settings)
	print("script update")
	weekday = obs.obs_data_get_int(settings, "weekday")
	time = obs.obs_data_get_int(settings, "time")
	
	start_scene = obs.obs_data_get_string(settings, "start_scene")

	preshow_duration = obs.obs_data_get_int(settings, "preshow_duration")
	countdown_duration = obs.obs_data_get_int(settings, "countdown_duration")
	countdown_offset = obs.obs_data_get_int(settings, "countdown_offset")

	auto_start_streaming = obs.obs_data_get_bool(settings, "auto_start_streaming")

	auto_start_recording = obs.obs_data_get_int(settings, "auto_start_recording")
end