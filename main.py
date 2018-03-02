import requests
import json
import getpass

#change the variables below
username = getpass.getpass("ID: ")
password = getpass.getpass("pw: ")
target_id = getpass.getpass("target ID: ")


origin_url = 'https://www.instagram.com'
login_url = origin_url + '/accounts/login/ajax/'
user_agent = 'Chrome/59.0.3071.115'

#login ig and get cookies
session = requests.Session()
session.headers = {'user-agent': user_agent}
session.headers.update({'Referer': origin_url})

req = session.get(origin_url)
try:
    req.raise_for_status()
except Exception as exc:
    print('problem occur: %s' % (exc))
    exit()

session.headers.update({'X-CSRFToken': req.cookies['csrftoken']})
login_data = {'username': username, 'password': password}
login = session.post(login_url, data=login_data, allow_redirects=True)
try:
    login.raise_for_status()
except Exception as exc:
    print('problem occur: %s' % (exc))
    exit()

session.headers.update({'X-CSRFToken': login.cookies['csrftoken']})
cookies = login.cookies
login_text = json.loads(login.text)


#Get url of pictures,
#if the post has single picture, get url,
#if the post has multiple pictures, get the url of the post,
#request the url and get all urls of pictures
#save all urls in pics_url_list
def handle_12_posts(data, origin_url, target_id):

    pics_url_list = []
    
    for i in data['user']['media']['nodes']:
        
        typename = str(i['__typename'])
        
        if typename == "GraphImage":
            pic_url = str(i['display_src'])
            print(pic_url)
            pics_url_list.append(pic_url)

        if typename == "GraphSidecar":
            
            code = str(i['code'])
            post_url = origin_url + '/p/' + code + '/?__a=1'

            response = session.get(post_url)
            try:
                response.raise_for_status()
            except Exception as exc:
	            print('problem occur: %s' % (exc))
	            exit()

            post_data = response.json()
            node_arr = post_data['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']

            for node in node_arr:
                pic_url = node['node']['display_url']
                print(pic_url)
                pics_url_list.append(pic_url)

    return pics_url_list


def get_end_cursor(data):
    
    return str(data['user']['media']['page_info']['end_cursor'])


def refresh_url(origin_url, target_id, end_cursor):
    return str(origin_url + '/' + target_id + '/?__a=1&max_id=' + end_cursor)


def main():

    pics_url_list = []

    target_url = origin_url + '/' + target_id +'/?__a=1' 
    req = session.get(target_url)
    try:
        req.raise_for_status()
    except Exception as exc:
        print('problem occur: %s' % (exc))
        exit()

    data = req.json()

    not_last = True

    #Only 12 posts are received when directing to one's profile,
    #we have to get the end_cursor and redirect to get the next 12 posts,
    #keep redirecting until number of posts is less than 12  
    while(not_last):
        pics_url_list.extend(handle_12_posts(data, origin_url, target_id))
        end_cursor = get_end_cursor(data)
        target_url = refresh_url(origin_url, target_id, end_cursor)
        

        data = session.get(target_url).json()
        if(len(data['user']['media']['nodes']) < 12):
            break

    # Last posts
    pics_url_list.extend(handle_12_posts(data, origin_url, target_id))

    #download all pictures
    for url in pics_url_list:

        print('url = ' + url)

        with open(url.split('/').pop(),'wb') as handle:
            response = session.get(url, stream=True)

            try:
                response.raise_for_status()
            except Exception as exc:
	            print('problem occur: %s' % (exc))
	            exit()

            for block in response.iter_content(15000):
                if not block:
                    break

                handle.write(block)


if __name__ == '__main__':
    main()
