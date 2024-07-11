# routes/streams.py
from flask import jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from services.streams import *
from routes import streams_bp
from utilities.utils import get_error_message, parse_query

# Returns a paginated list of live streams for a specific game ids or a user id
@streams_bp.route('/', methods=['GET'])
def get_game_streams():
    # game_id = request.args.get('game_id')
    #game_ids = request.args.getlist('game_id')
    game_ids_param = request.args.get('game_id')
    game_ids = [int(game_id) for game_id in game_ids_param.split(',')] if game_ids_param else []
    number_of_results = int(request.args.get('number_of_results', 50))
    user_id = request.args.get('user_id', None)
    user_login = request.args.get('user_login', None)
    language = request.args.get('language', None)
    cursor = request.args.get('cursor', None)

    if not game_ids and not user_id and not language and not user_login:
        return get_error_message('game_id, user_id, user_login or language')

    data, status_code = get_streams(game_ids, number_of_results, user_id, user_login, language, cursor, request.path)
    return jsonify(data), status_code

# Starts retrieving comments for a list of live streams
@streams_bp.route('/comments/start', methods=['POST'])
def start_comments_handler():
    data = request.get_json()

    if not data.get('caseId') and not data.get('taskId') and not data.get('streamers'):
        return get_error_message('caseId, taskId and streamers list')
    
    streamers_data, status_code = create_jobs_per_streamer(data.get("streamers"), data.get("taskId"))
    if len(streamers_data["streamers"]) == 0:
        return get_error_message("No Job created into the DB")
    response_data, status_code = retrieve_comments_start(data.get('caseId'), data.get('taskId'), streamers_data.get('streamers'))
    return jsonify(response_data), status_code

# Stops retrieving comments for a crawling id
@streams_bp.route('/comments/stop', methods=['POST'])
def stop_comments_handler():
    data = request.get_json()
    if not data.get('taskId'):
        return get_error_message('taskId')
    
    response_data, status_code = retrieve_comments_stop(data.get('taskId'))
    return jsonify(response_data), status_code

# Returns all the available tags for a list of games
@streams_bp.route('/tags', methods=['GET'])
def get_all_tags_route():
    game_ids_param = request.args.get('game_id')
    game_ids = [int(game_id) for game_id in game_ids_param.split(',')] if game_ids_param else []
    number_of_results = int(request.args.get('number_of_results', 150))
    user_id = request.args.get('user_id', None)
    user_login = request.args.get('user_login', None)
    language = request.args.get('language', None)
    languages = [str(lang) for lang in language.split(',')] if language else []
    crawl_id = request.args.get('crawl_id', None)

    if not game_ids and not user_id and not language and not user_login:
        return get_error_message('game_id, user_id, user_login or language')
    
    data, status_code = get_all_tags(crawl_id, game_ids, user_id, user_login, languages, "/streams/")
    return jsonify(data), status_code

# Returns the streamers which are associated with the given tag list
@streams_bp.route('/tags/search', methods=['GET'])
def get_streams_by_tags_route():
    tags_param = request.args.get('tags', None)
    tokens = parse_query(tags_param)
    print(f"Tokens: {tokens}")

    crawl_id = request.args.get('crawl_id')
    game_ids_param = request.args.get('game_ids')
    if (not tags_param) or (not crawl_id):
        return get_error_message("tags and the crawl_id")
    
    game_ids = [int(game_id) for game_id in game_ids_param.split(',')] if game_ids_param else []
    resp = []
    for game_id in game_ids:
        
        tokens_copy = tokens[:]
        print(f"\n\nGAME ID: {game_id}\n-----------------------\nTokens: {tokens_copy}")
        data, status_code = evaluate_expression(tokens_copy, crawl_id, game_id)
        if status_code != 200: return data, status_code
        resp.extend(data)

    print(f"The total length is {len(resp)}")
    return jsonify({"data": resp}), status_code

scheduler = BackgroundScheduler()
scheduler.start()

# A global dictionary to keep track of jobs
jobs = {}

@streams_bp.route('/comments/background', methods=['POST'])
def crawl_streams_background_route():
    data = request.get_json()
    case_id = data.get('caseId')
    task_id = data.get('taskId')
    game_ids = data.get('game_ids')
    languages = data.get('languages', None)
    tags = data.get('tags', None)
    tags = [tag.lower() for tag in tags]
    period = data.get('period', 6)

    print(f"The games {game_ids}\nlangs {languages}\ntags {tags}\nperiod {period}")
    job_id = task_id
    if job_id in jobs: return jsonify({"error": "Task Id is already running"}), 400
    scheduler.add_job(
            crawl_streams_background,
            trigger=DateTrigger(run_date=datetime.datetime.now()),
            args=[case_id, task_id, game_ids, languages, tags],
            id=f"{job_id}_immediate",
            replace_existing=True
    )

    jobs[job_id] = scheduler.add_job(
        crawl_streams_background,
        trigger=IntervalTrigger(hours=period),
        args=[case_id, task_id, game_ids, languages, tags],
        id=job_id,
        replace_existing=True
    )

    print(f"Scheduled job {job_id} to run immediately and then every {period} hours")
    print(f"All the created job ids are:\n{jobs}\n\n")
    return jsonify({"message": "Schedule started", "jobId": job_id})

@streams_bp.route('/comments/background', methods=['DELETE'])
def remove_job():
    # job_id = request.args.get('jobId')
    task_id = request.args.get('taskId')
    print(f"Task id {task_id}")
    if task_id in jobs:
        scheduler.remove_job(task_id)
        jobs.pop(task_id, None)

        response_data, status_code = retrieve_comments_stop(task_id)
        remove_taskId_from_already_crawled(task_id)
        return jsonify(response_data), status_code
    else:
        return jsonify({"message": "Job ID not found"}), 404