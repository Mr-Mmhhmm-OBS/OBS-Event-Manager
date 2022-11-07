import obspython as obs
import math
from datetime import time, timedelta, datetime

version = "2.3"

days_of_week = [ "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" ]

weekday = 0

start_scene = ""

preshow_duration = 1*60*5
event_start = 37800 # 10:25 AM

text_source = ""
countdown_final_text = "Live Soon!"

manage_streaming = True
manage_recording = True

closing_scene = ""
stop_streaming_delay = 60
stop_recording_delay = 0	

def on_event(event):
	if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
		if get_current_scene_name() == closing_scene:
			if manage_recording and obs.obs_frontend_recording_active():
				if stop_recording_delay == 0:
					stop_recording()
				else:
					obs.timer_add(stop_recording, stop_recording_delay * 1000)
			if manage_streaming and obs.obs_frontend_streaming_active():
				if stop_streaming_delay == 0:
					stop_streaming()
				else:
					obs.timer_add(stop_streaming, stop_streaming_delay * 1000)
		else:
			if manage_recording and obs.obs_frontend_recording_active():
				obs.timer_remove(stop_recording)
			if manage_streaming and obs.obs_frontend_streaming_active():
				obs.timer_remove(stop_streaming)
	elif not (obs.obs_frontend_streaming_active() or obs.obs_frontend_recording_active()) and (event == obs.OBS_FRONTEND_EVENT_STREAMING_STARTING or event == obs.OBS_FRONTEND_EVENT_RECORDING_STARTING) and get_current_scene_name() != start_scene:
		scenes = obs.obs_frontend_get_scenes()
		if scenes != None:
			for scene_source in scenes:
				print(str(obs.obs_source_get_type(scene_source)))
				scene_name = obs.obs_source_get_name(scene_source)
				if scene_name == start_scene:
					print(scene_name)
					obs.obs_frontend_set_current_scene(scene_source)
					break
			obs.source_list_release(scenes)	
	elif (event == obs.OBS_FRONTEND_EVENT_STREAMING_STOPPING and not obs.obs_frontend_recording_active()) or (event == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPING and not obs.obs_frontend_streaming_active()):
		obs.obs_frontend_remove_event_callback(on_event)

def update_countdown():
	text = ""
	t = diff_time(event_start).total_seconds()
	if t < 0:
		text = countdown_final_text
		obs.timer_remove(update_countdown)
	elif not (obs.obs_frontend_streaming_active() or obs.obs_frontend_recording_active()):
		text = ""
		obs.timer_remove(update_countdown)
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

def diff_time(start_int):
	now = datetime.now().time()
	now = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
	start = time(hour=math.floor(start_int / 60/ 60), minute = int((start_int / 60) % 60))
	start = timedelta(hours=start.hour, minutes=start.minute, seconds=start.second)
	return start - now

def get_current_scene_name():
	scene_source = obs.obs_frontend_get_current_scene()
	scene_name = obs.obs_source_get_name(scene_source)
	obs.obs_source_release(scene_source)
	return scene_name

def check_start():
	t = diff_time(event_start).total_seconds()
	if t > preshow_duration and not (obs.obs_frontend_streaming_active() or obs.obs_frontend_recording_active()):
		preshow_diff_t = diff_time(event_start-preshow_duration).total_seconds()
		set_text_source("Script Waiting: " + (">1h" if preshow_diff_t >60*60 else time(minute=math.floor(preshow_diff_t / 60), second=int(preshow_diff_t%60)).strftime("%M:%S")))
	elif t <= preshow_duration:
		obs.obs_frontend_add_event_callback(on_event)
		if manage_streaming:
			obs.obs_frontend_streaming_start()
		if manage_recording:
			obs.obs_frontend_recording_start()
		obs.timer_add(update_countdown, 1000)
		obs.timer_remove(check_start)

def stop_streaming():
	if manage_streaming and obs.obs_frontend_streaming_active() and get_current_scene_name() == closing_scene:
		obs.obs_frontend_streaming_stop()
	obs.timer_remove(stop_streaming)

def stop_recording():
	if manage_recording and obs.obs_frontend_recording_active() and get_current_scene_name() == closing_scene:
		obs.obs_frontend_recording_stop()
	obs.timer_remove(stop_recording)

def script_description():
	return "Automatically starts a scheduled event.\nv" + version

def event_start_list_modified(props, property, settings):
	event_start_list = obs.obs_properties_get(props, "preshow_duration")
	obs.obs_property_list_clear(event_start_list)
	for i in range(0,4):
		seconds = i*60*5
		obs.obs_property_list_add_int(event_start_list, time(hour=math.floor((event_start-seconds)/60/60), minute=int((event_start-seconds)/60%60)).strftime("%I:%M %p"), seconds)
	return True

def closing_scene_modified(props, properties, settings):
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "stop_streaming_delay"), closing_scene != "" and manage_streaming)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "stop_recording_delay"), closing_scene != "" and manage_recording)
	return True

def on_property_modified(props, property, settings):
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "start_scene"), manage_streaming or manage_recording)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "weekday"), (manage_streaming or manage_recording) and start_scene != "")
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "event_start"), (manage_streaming or manage_recording) and start_scene != "")
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "preshow_duration"), (manage_streaming or manage_recording) and start_scene != "")
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "text_source"), (manage_streaming or manage_recording) and start_scene != "")
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "countdown_final_text"), (manage_streaming or manage_recording) and text_source != "" and start_scene != "")
	
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "closing_scene"), manage_streaming or manage_recording)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "stop_streaming_delay"), closing_scene != "" and manage_streaming)
	obs.obs_property_set_enabled(obs.obs_properties_get(props, "stop_recording_delay"), closing_scene != "" and manage_recording)
	return True

def script_properties():
	props = obs.obs_properties_create()

	p = obs.obs_properties_add_bool(props, "manage_streaming", "Manage Streaming")
	obs.obs_property_set_modified_callback(p, on_property_modified)
	p = obs.obs_properties_add_bool(props, "manage_recording", "Manage Recording")
	obs.obs_property_set_modified_callback(p, on_property_modified)

	auto_start_group = obs.obs_properties_create()
	obs.obs_properties_add_group(props, "auto_start_group", "Auto Start", obs.OBS_GROUP_NORMAL, auto_start_group)

	p = obs.obs_properties_add_list(auto_start_group, "start_scene", "Start Scene", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	obs.obs_property_set_enabled(p, manage_streaming or manage_recording)
	obs.obs_property_set_modified_callback(p, on_property_modified)
	obs.obs_property_list_add_string(p, "--Disabled--", "")
	scene_names = obs.obs_frontend_get_scene_names()
	if scene_names != None:
		for scene_name in scene_names:
			obs.obs_property_list_add_string(p, scene_name, scene_name)

	schedule_group = obs.obs_properties_create()
	obs.obs_properties_add_group(auto_start_group, "schedule_group", "Schedule", obs.OBS_GROUP_NORMAL, schedule_group)

	p = obs.obs_properties_add_list(schedule_group, "weekday", "Day of Week", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
	obs.obs_property_set_enabled(p, (manage_streaming or manage_recording) and start_scene != "")
	for i, day_of_week in enumerate(days_of_week):
		obs.obs_property_list_add_int(p, day_of_week, i)

	p = obs.obs_properties_add_list(schedule_group, "preshow_duration", "Livestream Start", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
	obs.obs_property_set_enabled(p, (manage_streaming or manage_recording) and start_scene != "")
	obs.obs_property_list_clear(p)
	for i in range(4):
		seconds = i*60*5
		obs.obs_property_list_add_int(p, time(hour=math.floor((event_start-seconds)/60/60), minute=int((event_start-seconds)/60%60)).strftime("%I:%M %p"), seconds)

	p = obs.obs_properties_add_list(schedule_group, "event_start", "Event Start", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
	obs.obs_property_set_enabled(p, (manage_streaming or manage_recording) and start_scene != "")
	obs.obs_property_set_modified_callback(p, event_start_list_modified)
	for i in range(288):
		obs.obs_property_list_add_int(p, time(hour=math.floor(i/12), minute=(i%12)*5).strftime("%I:%M %p"), int((i/12)*60*60))

	text_source_list = obs.obs_properties_add_list(auto_start_group, "text_source", "Text Source", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	obs.obs_property_set_enabled(text_source_list, (manage_streaming or manage_recording) and start_scene != "")
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

	p = obs.obs_properties_add_text(auto_start_group, "countdown_final_text", "Countdown Final Text", obs.OBS_TEXT_DEFAULT)
	obs.obs_property_set_enabled(p, (manage_streaming or manage_recording) and text_source != "" and start_scene != "")

	auto_stop_group = obs.obs_properties_create()
	obs.obs_properties_add_group(props, "auto_stop_group", "Auto Stop", obs.OBS_GROUP_NORMAL, auto_stop_group)

	p = obs.obs_properties_add_list(auto_stop_group, "closing_scene", "Closing Scene", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
	obs.obs_property_set_enabled(p, manage_streaming or manage_recording)
	obs.obs_property_set_modified_callback(p, closing_scene_modified)
	obs.obs_property_list_add_string(p, "--Disabled--", "")
	scene_names = obs.obs_frontend_get_scene_names()
	if scene_names != None:
		for scene_name in scene_names:
			obs.obs_property_list_add_string(p, scene_name, scene_name)

	p = obs.obs_properties_add_int(auto_stop_group, "stop_streaming_delay", "Streaming Delay", 0, 300, 15)
	obs.obs_property_set_enabled(p, manage_streaming and closing_scene != "")
	p = obs.obs_properties_add_int(auto_stop_group, "stop_recording_delay", "Recording Delay", 0, 120, 5)
	obs.obs_property_set_enabled(p,  manage_recording and closing_scene != "")

	return props

def script_defaults(settings):
	obs.obs_data_set_default_int(settings, "weekday", weekday)
	obs.obs_data_set_default_int(settings, "event_start", event_start)

	obs.obs_data_set_default_int(settings, "preshow_duration", preshow_duration)

	obs.obs_data_set_default_string(settings, "countdown_final_text", countdown_final_text)

	obs.obs_data_set_default_bool(settings, "manage_streaming", manage_streaming)
	obs.obs_data_set_default_bool(settings, "manage_recording", manage_recording)	

def script_update(settings):
	global weekday
	weekday = obs.obs_data_get_int(settings, "weekday")

	global event_start
	event_start = obs.obs_data_get_int(settings, "event_start")
	
	global start_scene
	start_scene = obs.obs_data_get_string(settings, "start_scene")

	global manage_streaming
	manage_streaming = obs.obs_data_get_bool(settings, "manage_streaming")
	global manage_recording
	manage_recording = obs.obs_data_get_bool(settings, "manage_recording")

	global preshow_triggered
	preshow_triggered = False
	global preshow_duration
	preshow_duration = obs.obs_data_get_int(settings, "preshow_duration")

	global text_source
	text_source = obs.obs_data_get_string(settings, "text_source")
	global countdown_final_text
	countdown_final_text = obs.obs_data_get_string(settings, "countdown_final_text")

	global stop_streaming_delay
	stop_streaming_delay = obs.obs_data_get_int(settings, "stop_streaming_delay")
	global stop_recording_delay
	stop_recording_delay = obs.obs_data_get_int(settings, "stop_recording_delay")
	global closing_scene
	closing_scene = obs.obs_data_get_string(settings, "closing_scene")	
	
	obs.timer_remove(check_start)
	obs.timer_remove(update_countdown)
	set_text_source("")
	if (manage_streaming or manage_recording) and start_scene != "" and weekday == datetime.now().weekday() and diff_time(event_start).total_seconds() > 0 and not (obs.obs_frontend_streaming_active() or obs.obs_frontend_recording_active()):
		obs.timer_add(check_start, 1000)