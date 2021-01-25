obs=obslua

local version = "1.3""

days_of_week = { "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday" }

weekday = -1
livestream_start = 37500 -- 10:25 AM

start_scene = ""

preshow_triggered = false
preshow_duration = 1*60*5

text_source = ""
countdown_duration = 60
countdown_offset = -10
countdown_final_text = "Live Soon!"

video_source = ""

auto_start_streaming = true
auto_start_recording = true

function event_callback_start_recording(event)
	if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED then
		if auto_start_recording and not obs.obs_frontend_recording_active() then
			obs.obs_frontend_recording_start()
		end
	end
end

function show_video_source(show)
	local scene = obs.obs_frontend_get_current_scene()
    local sceneitems = obs.obs_scene_enum_items(scene)
	if sceneitems ~= nil then
		for key, sceneitem in ipairs(sceneitems) do
			local source = obs.obs_sceneitem_get_source(sceneitem)
			if obs.obs_source_get_name(source) == video_source then
				obs.obs_sceneitem_set_visible(sceneitem, show)
				break
			end
			obs.obs_source_release(source)
		end
		obs.sceneitem_list_release(sceneitems)
	end
end

function update_countdown()
	local text = ""
	local t = diff_time() - countdown_offset
	if t < 0 then
		text = countdown_final_text
		show_video_source(true)
		obs.remove_current_callback()
	else
		text = string.format("%02d:%02d", math.floor(t / 60), t % 60)
	end

	set_text_source(text)
end

function set_text_source(text)
	local source = obs.obs_get_source_by_name(text_source)

	if source ~= nil then
		local settings = obs.obs_data_create()
		obs.obs_data_set_string(settings, "text", text)
		obs.obs_source_update(source, settings)
		obs.obs_data_release(settings)
		obs.obs_source_release(source)
	end
end

function diff_time()
	start_time = livestream_start + preshow_duration
	local start_time = os.time{
		year = os.date("%Y"), 
		month = os.date("%m"), 
		day = os.date("%d"), 
		hour = math.floor(start_time / 60/ 60), 
		min = (start_time / 60) % 60,
		sec = start_time % 60
	}
	return os.difftime(start_time, os.time())
end

function get_current_scene_name()
	local scene = obs.obs_frontend_get_current_scene()
	local scene_name = obs.obs_source_get_name(scene)
	obs.obs_source_release(scene);
	return scene_name
end

function check_start()
	local t = diff_time()
	if t > preshow_duration and (auto_start_streaming or auto_start_recording) and not (obs.obs_frontend_streaming_active() or obs.obs_frontend_recording_active()) then
		local text = "Waiting"
		for i=0,((t%3)-2)*-1 do
			text = text .. "."
		end
		set_text_source(text)
	else
		if t <= preshow_duration and not preshow_triggered then
			preshow_triggered = true
			if get_current_scene_name() ~= start_scene then
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

			if auto_start_streaming then
				obs.obs_frontend_streaming_start()
			end

			if auto_start_recording then
				obs.obs_frontend_add_event_callback(event_callback_start_recording)
			end
		end

		obs.timer_add(update_countdown, 1000)
		obs.remove_current_callback()
	end
end

function script_description()
	return "Automatically starts a scheduled event.\nv" .. version
end

function livestream_start_list_modified(props, property, settings)
	local event_start_list = obs.obs_properties_get(props, "preshow_duration")
	obs.obs_property_list_clear(event_start_list)
		for i=0,4 do
		local seconds = i*60*5
		obs.obs_property_list_add_int(event_start_list, string.format("%02d:%02d", math.floor((livestream_start+seconds)/60/60), (livestream_start+seconds)/60%60), i*60*5)
	end
	return true
end

function on_property_modified(props, property, settings)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "livestream_start"), weekday > -1)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "preshow_duration"), weekday > -1)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "start_scene"), weekday > -1)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "auto_start_streaming"), weekday > -1)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "auto_start_recording"), weekday > -1)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "text_source"), weekday > -1)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "countdown_offset"), weekday > -1 and text_source ~= "")
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "countdown_final_text"), weekday > -1 and text_source ~= "")
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "video_source"), weekday > -1)
	return true
end

function script_properties()
	local props = obs.obs_properties_create()
	
	local schedule_group = obs.obs_properties_create()
	local p = obs.obs_properties_add_list(schedule_group, "weekday", "Day of Week", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
	obs.obs_property_set_modified_callback(p, on_property_modified)
	obs.obs_property_list_add_int(p, "--Disabled--", -1)
	for i in pairs(days_of_week) do
		obs.obs_property_list_add_int(p, days_of_week[i], i - 1)
	end
		
	p = obs.obs_properties_add_list(schedule_group, "livestream_start", "Livestream Start", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
	obs.obs_property_set_enabled(p, weekday > -1)
	obs.obs_property_set_modified_callback(p, livestream_start_list_modified)
	for i=0,(24*12)-1 do
		obs.obs_property_list_add_int(p, string.format("%02d:%02d", math.floor(i/12), (i%12) * 5), (i/12)*60*60)
	end
		
	p = obs.obs_properties_add_list(schedule_group, "preshow_duration", "Event Start", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
	obs.obs_property_set_enabled(p, weekday > -1)
	obs.obs_property_list_clear(p)
	for i=0,4 do
		local seconds = i*60*5
		obs.obs_property_list_add_int(p, string.format("%02d:%02d", math.floor((livestream_start+seconds)/60/60), (livestream_start+seconds)/60%60), i*60*5)
	end
	obs.obs_properties_add_group(props, "schedule_group", "Schedule", obs.OBS_GROUP_NORMAL, schedule_group)

	p = obs.obs_properties_add_list(props, "start_scene", "Start Scene", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	obs.obs_property_set_enabled(p, weekday > -1)
	local scene_names = obs.obs_frontend_get_scene_names()
	if scene_names ~= nil then
		for _, scene_name in ipairs(scene_names) do
			obs.obs_property_list_add_string(p, scene_name, scene_name)
		end
	end
	
	p = obs.obs_properties_add_bool(props, "auto_start_streaming", "Auto Start Streaming")
	obs.obs_property_set_enabled(p, weekday > -1)
	p = obs.obs_properties_add_bool(props, "auto_start_recording", "Auto Start Recording")
	obs.obs_property_set_enabled(p, weekday > -1)

	local text_source_list = obs.obs_properties_add_list(props, "text_source", "Text Source", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	obs.obs_property_set_enabled(text_source_list, weekday > -1)
	obs.obs_property_set_modified_callback(text_source_list, on_property_modified)
	obs.obs_property_list_add_string(text_source_list, "--Disabled--", "")

	obs.obs_property_set_enabled(p, weekday > -1 and text_source ~= "")
	p = obs.obs_properties_add_int_slider(props, "countdown_offset", "Countdown Offset", -300, 300, 10)
	obs.obs_property_set_enabled(p, weekday > -1 and text_source ~= "")
	p = obs.obs_properties_add_text(props, "countdown_final_text", "Countdown Final Text", obs.OBS_TEXT_DEFAULT)
	obs.obs_property_set_enabled(p, weekday > -1 and text_source ~= "")

	local video_source_list = obs.obs_properties_add_list(props, "video_source", "Video Source", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	obs.obs_property_set_enabled(video_source_list, weekday > -1)
	obs.obs_property_list_add_string(video_source_list, "--Disabled--", "")
	local sources = obs.obs_enum_sources()
	if sources ~= nil then
		for _, source in ipairs(sources) do
			source_id = obs.obs_source_get_unversioned_id(source)
			if source_id == "text_gdiplus" or source_id == "text_ft2_source" then
				local name = obs.obs_source_get_name(source)
				obs.obs_property_list_add_string(text_source_list, name, name)
			end
			if source_id == "dshow_input" then
				local name = obs.obs_source_get_name(source)
				obs.obs_property_list_add_string(video_source_list, name, name)
			end
		end
	end
	obs.source_list_release(sources)

	return props
end

function script_defaults(settings)
	obs.obs_data_set_default_int(settings, "weekday", weekday)
	obs.obs_data_set_default_int(settings, "livestream_start", livestream_start)

	obs.obs_data_set_default_int(settings, "preshow_duration", preshow_duration)

	obs.obs_data_set_default_int(settings, "countdown_offset", countdown_offset)
	obs.obs_data_set_default_string(settings, "countdown_final_text", countdown_final_text)

	obs.obs_data_set_default_bool(settings, "auto_start_streaming", auto_start_streaming)
	obs.obs_data_set_default_bool(settings, "auto_start_recording", auto_start_recording)
end

function script_update(settings)
	weekday = obs.obs_data_get_int(settings, "weekday")
	livestream_start = obs.obs_data_get_int(settings, "livestream_start")
	
	start_scene = obs.obs_data_get_string(settings, "start_scene")

	auto_start_streaming = obs.obs_data_get_bool(settings, "auto_start_streaming")
	auto_start_recording = obs.obs_data_get_bool(settings, "auto_start_recording")

	preshow_triggered = false
	preshow_duration = obs.obs_data_get_int(settings, "preshow_duration")

	text_source = obs.obs_data_get_string(settings, "text_source")
	countdown_offset = obs.obs_data_get_int(settings, "countdown_offset") * -1
	countdown_final_text = obs.obs_data_get_string(settings, "countdown_final_text")

	video_source = obs.obs_data_get_string(settings, "video_source")

	obs.timer_remove(check_start)
	obs.timer_remove(update_countdown)
	show_video_source(false)
	set_text_source("")
	if weekday == tonumber(os.date("%w")) and diff_time() > countdown_offset and not (obs.obs_frontend_streaming_active() or obs.obs_frontend_recording_active()) then
		obs.timer_add(check_start, 1000)
	end
end