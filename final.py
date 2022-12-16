
import json
import requests
from flask import Flask
from flask import render_template, request
from datetime import datetime
import pandas as pd

CACHE_FILENAME = "nba_schedule.json"
BASE_URL = "http://api.sportradar.us/nba/trial/v7/"
API_KEY = "nrx8c9ta6wwtgnrkcyw4n22g"

class Node:
    def __init__(self, date, val, left=None, right=None, parent=None):
        self.date = date
        if isinstance(val, list):
            self.val = val
        else:
            self.val = [val]
        self.left = left
        self.right = right
        self.parent = parent

    def hasLeft(self):
        return self.left

    def hasRight(self):
        return self.right

class Tree:
    def __init__(self):
        self.root = None
    
    def depth(self, root):
        if root is None:
            return 0
        leftDepth = self.depth(root.left) + 1
        rightDepth = self.depth(root.right) + 1
        height = rightDepth
        if leftDepth > rightDepth:
            height = leftDepth
        return height

    def put(self, date, val):
        date = pd.Timestamp(date).date()
        if self.root:
            self.add(date, val, self.root)
        else:
            self.root = Node(date, val)

    def add(self, date, val, current):
        date = pd.Timestamp(date).date()
        if date < current.date:
            if current.hasLeft():
                self.add(date, val, current.left)
            else:
                current.left = Node(date, val, parent=current)
        elif date == current.date:
            current.val.append(val)
        else:
            if current.hasRight():
                self.add(date, val, current.right)
            else:
                current.right = Node(date, val, parent=current)
    
    def search_for_day(self, date):
        if self.root:
            res = self.get(date, self.root)
            if res:
                return res.val
            else:
                return None
        else:
            return None
    
    def get(self, date, current):
        date = pd.Timestamp(date).date()
        if not current:
            return None
        elif current.date == date:
            return current
        elif date < current.date:
            return self.get(date, current.left)
        else:
            return self.get(date, current.right)
    
    def print_tree(self, root):

        '''
        打印一棵二叉树，二叉树节点值为0~9 10个整数或者26个大小写英文字母
        使用/\模拟左右分支,如下所示
                e                           
             /     \
            c       g
           / \     / \
          b   d   f   h
         /
        a
        但是在打印满二叉树时，最多打印三层，对于深度为4的二叉树，存在节点冲突，无法打印
        '''
        if root is None:
            return

        current = self.depth(root)

        max_word = 3 * (2 ** (current - 1)) - 1
        node_space = int(max_word / 2)  
 
        queue1 = [[self.root, node_space + 1]]
        queue2 = []
        while queue1:

            i_position = []

            for i in range(len(queue1)):
                node = queue1[i][0]
                i_space = queue1[i][1] - 1  

                if node.date == self.root.date:
                    i_space -= 2

                if node.left is not None:
                    i_position.append([i_space, '/'])
                    queue2.append([node.left, i_space - 1])

                i_space += 2

                if node.date == self.root.date:
                    i_space += 4
                if node.right is not None:
                    i_position.append([i_space, '\\'])
                    queue2.append([node.right, i_space + 1])
            if len(queue1) > 0:
                last_node = queue1[len(queue1) - 1][1]
                index = 0
                for i in range(last_node + 1):
                    if index < len(queue1) and i == queue1[index][1]:
                        print(queue1[index][0].val, end='')
                        index += 1
                    else:
                        print(' ', end='')
            print()
            index = 0
            if len(i_position) > 0:
                for i in range(i_position[len(i_position) - 1][0] + 1):
                    if i == i_position[index][0]:
                        print(i_position[index][1], end='')
                        index += 1
                    else:
                        print(' ', end='')
            print()
            # update queue1 and queue2
            queue1 = []
            while queue2:
                queue1.append(queue2.pop(0))
            node_space -= 2

SCHEDULE_TREE = Tree()

def get_url(url):
    resp = requests.get(url)
    json_str = resp.text
    json_data = json.loads(json_str)
    return json_data

def open_cache():
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

FIB_CACHE = open_cache()

def get_url_with_cache(url):
    if url in FIB_CACHE:
        return FIB_CACHE[url]
    else:
        FIB_CACHE[url] = get_url(url)
        save_cache(FIB_CACHE)
        return FIB_CACHE[url]

def get_games(SCHEDULE_TREE):
    '''
    Get 2022 regular season schedules and their box scores, and store the data into tree

    param:
        SCHEDULE_TREE: A global tree structure variable for storing games data
    '''
    nba_url = '{}en/games/2022/REG/schedule.json?api_key={}'.format(BASE_URL, API_KEY)
    game_json = get_url_with_cache(nba_url)
    games = game_json['games']
    date = datetime.now()
    ts = pd.Timestamp(date).date()
    for game in games:
        game_date = pd.to_datetime(game['scheduled'], format="%Y-%m-%d").replace(tzinfo=None).date()
        if ts > game_date:
            SCHEDULE_TREE.put(game_date, '{} vs {} {}:{}'.format(game['home']['alias'], 
                            game['away']['alias'], game['home_points'], game['away_points']))
        else:
            SCHEDULE_TREE.put(game_date, '{} vs {}'.format(game['home']['alias'], 
                            game['away']['alias']))
    #return SCHEDULE_TREE        

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", title="NBA Daily Scores")

@app.route('/daily_schedule', methods=['POST'])
def movie_detail():
    date = pd.to_datetime(request.form['date'], format="%Y-%m-%d").replace(tzinfo=None).date()
    pretty_date = date.strftime("%b %d, %Y")
    daily_schedule = SCHEDULE_TREE.search_for_day(date)
    if daily_schedule is None:
        daily_schedule = ["No Game Today"]
    return render_template('daily_schedule.html', date = date, 
                                schedule_list = daily_schedule,
                                pretty_date = pretty_date)
if __name__ == "__main__":
    get_games(SCHEDULE_TREE)
    #SCHEDULE_TREE.print_tree(SCHEDULE_TREE.root)
    app.run(debug=True)
    #app.run(host="0.0.0.0", port=8080, debug=True)



