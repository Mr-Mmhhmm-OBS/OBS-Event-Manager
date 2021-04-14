import obspython as obs
import math
from datetime import time, timedelta, datetime

version = "2.0"

days_of_week = [ "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" ]

weekday = -1
livestream_start = 37500 # 10:25 AM

start_scene = ""

preshow_triggered = False
preshow_duration = 1*60*5

text_source = ""
countdown_duration = 60
countdown_offset = -10
countdown_final_text = "Live Soon!"

auto_start_streaming = True
auto_start_recording = True

def event_callback_start_recording(event):
	if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
		if auto_start_recording and not obs.obs_frontend_recording_active():
			obs.obs_frontend_recording_start()

def update_countdown():
	text = ""
	t = diff_time().total_seconds() - countdown_offset
	if t < 0:
		text = countdown_final_text
		obs.remove_current_callback()
	else:
		text = time(minute=math.floor(t / 60), second=int(t%60)).strftime("%M:%S")
	set_text_source(text)

def set_text_source(text):
	source = obs.obs_get_source_by_name(text_source)
	if source != None:
		settings = obs.obs_data_create()
		obs.obs_data_set_string(settings, "text", text)
		obs.obs_source_update(source, settings)
		obs.obs_data_release(settings)
		obs.obs_source_release(source)

def diff_time():
	now = datetime.now().time()
	now = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
	start = time(hour=math.floor((livestream_start+preshow_duration) / 60/ 60), minute = int(((livestream_start+preshow_duration) / 60) % 60))
	start = timedelta(hours=start.hour, minutes=start.minute, seconds=start.second)
	return start - now

def get_current_scene_name():
	scene = obs.obs_frontend_get_current_scene()
	scene_name = obs.obs_source_get_name(scene)
	obs.obs_source_release(scene)
	return scene_name

def check_start():
	global preshow_triggered

	t = diff_time().total_seconds()
	if t > preshow_duration and (auto_start_streaming or auto_start_recording) and not (obs.obs_frontend_streaming_active() or obs.obs_frontend_recording_active()):
		set_text_source("Waiting" + ("".join([ "." for i in range(int(t)%4)])))
	else:
		if t <= preshow_duration and not preshow_triggered:
			preshow_triggered = True
			if get_current_scene_name() != start_scene:
				scenes = obs.obs_frontend_get_scenes()
				if scenes != None:
					for scene in scenes:
						scene_name = obs.obs_source_get_name(scene);
						if scene_name == start_scene:
							obs.obs_frontend_set_current_scene(scene)
							break
				obs.source_list_release(scenes)
			if auto_start_streaming:
				obs.obs_frontend_streaming_start()
			if auto_start_recording:
				obs.obs_frontend_add_event_callback(event_callback_start_recording)
		obs.timer_add(update_countdown, 1000)
		obs.remove_current_callback()

def script_description():
	return "Automatically starts a scheduled event.\nv" + version

def livestream_start_list_modified(props, property, settings):
	event_start_list = obs.obs_properties_get(props, "preshow_duration")
	obs.obs_property_list_clear(event_start_list)
	for i in range(0,4):
		seconds = i*60*5
		obs.obs_property_list_add_int(event_start_list, time(hour=math.floor((livestream_start+seconds)/60/60), minute=int((livestream_start+seconds)/60%60)).strftime("%I:%M %p"), seconds)
	return True

def on_property_modified(props, property, settings):
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "livestream_start"), weekday > -1)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "preshow_duration"), weekday > -1)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "start_scene"), weekday > -1)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "auto_start_streaming"), weekday > -1)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "auto_start_recording"), weekday > -1)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "text_source"), weekday > -1)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "countdown_offset"), weekday > -1 and text_source != "")
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "countdown_final_text"), weekday > -1 and text_source != "")
	return True

def script_properties():
	props = obs.obs_properties_create()
	
	schedule_group = obs.obs_properties_create()
	p = obs.obs_properties_add_list(schedule_group, "weekday", "Day of Week", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
	obs.obs_property_set_modified_callback(p, on_property_modified)
	obs.obs_property_list_add_int(p, "--Disabled--", -1)
	for i, day_of_week in enumerate(days_of_week):
		obs.obs_property_list_add_int(p, day_of_week, i)
	p = obs.obs_properties_add_list(schedule_group, "livestream_start", "Livestream Start", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
	obs.obs_property_set_enabled(p, weekday > -1)
	obs.obs_property_set_modified_callback(p, livestream_start_list_modified)
	for i in range(288):
		obs.obs_property_list_add_int(p, time(hour=math.floor(i/12), minute=(i%12)*5).strftime("%I:%M %p"), int((i/12)*60*60))
		
	p = obs.obs_properties_add_list(schedule_group, "preshow_duration", "Event Start", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
	obs.obs_property_set_enabled(p, weekday > -1)
	obs.obs_property_list_clear(p)
	for i in range(4):
		seconds = i*60*5
		obs.obs_property_list_add_int(p, time(hour=math.floor((livestream_start+seconds)/60/60), minute=int((livestream_start+seconds)/60%60)).strftime("%I:%M %p"), seconds)
	obs.obs_properties_add_group(props, "schedule_group", "Schedule", obs.OBS_GROUP_NORMAL, schedule_group)

	p = obs.obs_properties_add_list(props, "start_scene", "Start Scene", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	obs.obs_property_set_enabled(p, weekday > -1)
	scene_names = obs.obs_frontend_get_scene_names()
	if scene_names != None:
		for scene_name in scene_names:
			obs.obs_property_list_add_string(p, scene_name, scene_name)
	
	p = obs.obs_properties_add_bool(props, "auto_start_streaming", "Auto Start Streaming")
	obs.obs_property_set_enabled(p, weekday > -1)
	p = obs.obs_properties_add_bool(props, "auto_start_recording", "Auto Start Recording")
	obs.obs_property_set_enabled(p, weekday > -1)

	text_source_list = obs.obs_properties_add_list(props, "text_source", "Text Source", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	obs.obs_property_set_enabled(text_source_list, weekday > -1)
	obs.obs_property_set_modified_callback(text_source_list, on_property_modified)
	obs.obs_property_list_add_string(text_source_list, "--Disabled--", "")	

	sources = obs.obs_enum_sources()
	if sources != None:
		for source in sources:
			source_id = obs.obs_source_get_unversioned_id(source)
			if source_id == "text_gdiplus" or source_id == "text_ft2_source":
				name = obs.obs_source_get_name(source)
				obs.obs_property_list_add_string(text_source_list, name, name)
	obs.source_list_release(sources)

	p = obs.obs_properties_add_int_slider(props, "countdown_offset", "Countdown Offset", -300, 300, 10)
	obs.obs_property_set_enabled(p, weekday > -1 and text_source != "")
	p = obs.obs_properties_add_text(props, "countdown_final_text", "Countdown Final Text", obs.OBS_TEXT_DEFAULT)
	obs.obs_property_set_enabled(p, weekday > -1 and text_source != "")

	return props

def script_defaults(settings):
	obs.obs_data_set_default_int(settings, "weekday", weekday)
	obs.obs_data_set_default_int(settings, "livestream_start", livestream_start)

	obs.obs_data_set_default_int(settings, "preshow_duration", preshow_duration)

	obs.obs_data_set_default_int(settings, "countdown_offset", countdown_offset)
	obs.obs_data_set_default_string(settings, "countdown_final_text", countdown_final_text)

	obs.obs_data_set_default_bool(settings, "auto_start_streaming", auto_start_streaming)
	obs.obs_data_set_default_bool(settings, "auto_start_recording", auto_start_recording)

def script_update(settings):
	global weekday
	weekday = obs.obs_data_get_int(settings, "weekday")

	global livestream_start
	livestream_start = obs.obs_data_get_int(settings, "livestream_start")
	
	global start_scene
	start_scene = obs.obs_data_get_string(settings, "start_scene")

	global auto_start_streaming
	auto_start_streaming = obs.obs_data_get_bool(settings, "auto_start_streaming")
	global auto_start_recording
	auto_start_recording = obs.obs_data_get_bool(settings, "auto_start_recording")

	global preshow_triggered
	preshow_triggered = False
	global preshow_duration
	preshow_duration = obs.obs_data_get_int(settings, "preshow_duration")

	global text_source
	text_source = obs.obs_data_get_string(settings, "text_source")
	global countdown_offset
	countdown_offset = obs.obs_data_get_int(settings, "countdown_offset") * -1
	global countdown_final_text
	countdown_final_text = obs.obs_data_get_string(settings, "countdown_final_text")

	obs.timer_remove(check_start)
	obs.timer_remove(update_countdown)
	set_text_source("")
	if weekday == datetime.now().weekday() and diff_time().total_seconds() > countdown_offset and not (obs.obs_frontend_streaming_active() or obs.obs_frontend_recording_active()):
		obs.timer_add(check_start, 1000)