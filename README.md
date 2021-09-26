# Smart Hub

[![Build Status](https://app.travis-ci.com/jyoung90ie/qub-dissertation.svg?token=xyzLEs9qjL7SuD52KvT6&branch=main)](https://app.travis-ci.com/jyoung90ie/qub-dissertation) [![codecov](https://codecov.io/gh/jyoung90ie/qub-dissertation/branch/main/graph/badge.svg?token=46RL5224IH)](https://codecov.io/gh/jyoung90ie/qub-dissertation)


This platform was created as the final dissertation project for completion of the MSc Software Development at [Queen's University Belfast](https://www.qub.ac.uk/courses/postgraduate-taught/software-development-msc/). It demonstrates the skills I developed throughout the course.

The problem I chose to solve is that of home automation. Smart Hub is a system which handles the end-to-end communication, from hardware devices through to the devices/notificaionts that should be triggered when user-defined triggers have been met. This was a complex project which allowed me to advance my understanding of communication protocols (such as [MQTT](https://mqtt.org/)) and the importance of optimising code throughout (e.g. to avoid unneccessary database queries).

## Deployed Application

The application has been deployed on a Raspberry Pi on my home network and is accessible via [Smart Hub](http://smarthub-qub.duckdns.org/). 
## Demonstration Data & Accounts

To enable you to test the website functionality, a number of demo accounts, products, and, transactions have been created. You can access this data using the accounts below. 

| Email | Password | Desription |
| ----- | -------- | ---------- |
| `admin-account@smarthub.platform` | `this-is-a-test-account` | Admin account with access to [admin area](http://smarthub-qub.duckdns.org/). This has devices linked. |
| `demo-account@smarthub.platform` | `another-demo-account` | This account does not have any devices and is not an admin. |

## UX

Given the application has been designed to help the end-user manage smart home devices and develop custom automations, the UX is designed to be clean and intuitive. Navigation is consistent, colours, buttons, and positioning will all be familiar once the user has sampled each one. Given the complexity of the backend code, it was important for me to present a simple and intuitive user experience - which is what has been developed.

### User Stories

#### Smart Home User

As a customer I want to be able to...

- Manage all my devices from one platform
- Toggle my devices on and off on-demand
- Create automation routines
- Be notified when my automations have been triggered
- View logs of communications from my device
- Create custom device states that can be used as part of my automations
- Toggle automations on and off
- Secure my devices to my own account and ensure they are not accessible by other users


## Features

### Existing Features

This package enables you to build and deploy a functional smart home hub for managing your smart devices. At present, the platform supports only Zigbee devices, but future developments will expand this capability to incorporate other protocols, such as API based devices.

The package has been broken into individual apps, the features of which are detailed under each of the headings below.

#### Custom User Model

To capture additional user information, such as home location, I opted to override the default Django user model and create a custom one. This enabled me to store all the necessary user data in one object. It will also make any future user model changes easier to make.

Given the additional data input requirements, it was necessary to create custom forms to capture the additional information. This included overriding Django default forms, for example, the admin forms for adding/modifying user details.

#### Users

After researching authentication and authorisation, I made the decision to use `Django-allauth` which added a lot of funcionality, such as the ability to login with Social Accounts (e.g. Google), and limiting user account login attempts to improve security.

Outlined below are some of the key components of this app:

a) **Signup:** a custom form used to create a new user account with the custom user model. The username field is removed, with the email address used in it's placed. Given this is a smart hub platform, it made sense to capture the user's home location, so that future developments could use this as a trigger for automation.

b) **Login:** Enables users to login using their email address and password. 

c) **Logout:** Enables users to logout of their account. The user will be asked to confirm they wish to logout of their account, this prevents accidental logout. When a user logs out they will be unable to access any device/automation functionality - this is to prevent unauthorised users from change device data.

d) **Social login - Gmail:** Users can login using an existing Gmail account - this has been setup using Google's OAuth2 service and enables a user to hit the 'ground running' - with additional information captured under the user profile. To support this I created a custom `adapter` which overrode the default `django-allauth` implementation, using fields specific to this platform.

e) **Profile:** Here the user can update their personal details, including changing their home location.

f) **Profile - Change email:** A user can have multiple emails if they wish, this functionality is leveraged from `django-allauth`. The user can log in with all email addresses under their account. 

g) **Profile - Change password:** For security, a user must provide their current password alongside a new password before it will be accepted and updated.

#### Apps

a) **Mixins:**

Mixins are a `design pattern` which I have used to provide additional functionality or to override default Django functionality. To implement the mixin functionality they are inherited by the classes that need them.

`MakeRequestObjectAvailableInFormMixin`: the **Request object** is how Django passes data between views using the HTTP request, for example, the user session which identifies the specific user. By making this available in a form view, it enables action messages to be returned, e.g. for successfully creating a new device.

`AddUserToFormMixin`:  this mixin attaches the the **User object** to a specific form instance - this is used once a form has been validated, before it is saved as new object. An example is when creating a new device, it needs to be saved with the user that creates it.

`LimitResultsToUserMixin`: this filters a view's queryset for only results related to the specific user. This secures user objects to only the user that they belong to.

`UserHasLinkedDevice`: this mixin redirects a user from certain views (e.g. adding an event) if they do not have a linked device. This is in place to prevent creation of objects that rely on linked devices.

`FormSuccessMessageMixin`: this adds the ability for forms to return a message on success - each form can specify its own success message. It also handles errors by providing a generic error message.


b) **Forms:** 

`CustomChoiceField`: this overrides the default Django implementation for a HTML selection field. It prevents the default validation against the initial values for the field. This was needed because the initial value is empty, and when the page loads an XML Http Request (XHR) is made through JavaScript to fetch values to populate the list. This is used for form selection based on user input, for example, when a user selects a device for an event response, the metadata field will be updated to include options relevant to that device.

c) **Models:** 

`BaseAbstractModel`: this specifies a number of fields and default model ordering. The fields are audit type fields, i.e. when the object was created and when it was last updated. It also adds a more secure unique identifier `uuid`. By making this an abstract class, this means I do not need to repeat myself in each model.
#### MQTT

This is responsible for the handling of all MQTT communications for the platform.

a) **Listener:** Responsible for listening to MQTT broker and passing communications through to the platform for processing.

b) **Publisher:** Sends `device state` commands to MQTT broker when the user toggles a state or an event is invoked.

c) **Management Command:** Creates a shell command that can be run through the Django command line - using `python -m manage mqtt` which then starts the Smart Hub MQTT `Listener`.

d) **Toggle View:** This is an endpoint that is used to toggle a device's on/off state. It is invoked through an XHR form submission using JavaScript - from the user's prespective they simple click toggle. This endpoint will only accept `POST` requests to prevent it being accessed manually.

e) **Trigger View:** This is an endpoint that is used to invoke a user defined `device state`. It is invoked through an XHR form submission using JavaScript - from the user's prespective they simple click toggle. This endpoint will only accept `POST` requests to prevent it being accessed manually.


#### Devices

This handles the all functionality of user created devices, locations, and states.

a) **CRUD Device:** 

b) **CRUD DeviceLocation:** 

c) **CRUD DeviceState:** 

d) **Device Logs & Export:** 

e) **Device Metadata:** 

f) **Device States JSON:** 

g) **Redirects:**

h) **Customised Admin:** 

i) **Mixins:**

j) **Forms:**


### Zigbee Devices

This app is automatically passed information by the `MQTT app`, it will then determine whether a new `ZigbeeDevice` object should be created or will attach the communication to an existing object - dependent on the outcome of the processing.

a) **ZigbeeDevice:**

b) **ZigbeeMessage:**

c) **ZigbeeLog:**

d) **Customised Admin:**



#### Events

An `Event` is a way to create automation, by attaching `EventTriggers` and `EventResponses`. Events are processed by the `MQTT` app when new communications are received, to determine whether an event has been triggered or not. 

a) *CRUD Event:* 

b) **CRUD EventTrigger:** 

c) **CRUD EventResponse:** 

d) **Customised Admin:** 


#### Pages

The Pages app is used to website pages which are not related to any specific app. In this instance, the homepage and about us page are delivered via this app. It sets up the urls and delivers the templates to the end user.

#### Notifications

If a user wishes to receive a notification when an `Event` has been triggered, they will need to configure notification settings. At present, `Email` and `Pushbullet` notifications are supported.

a) **CRUD Notification:** 

b) **Pushbullet:** 

c) **Email:** 

d) **Redirects:** 

e) **Utils:**

Pushbullet API class

f) **Defines:**

g) **Customised Admin:** 

h) **Forms:**

#### Settings

The platform has been setup with two configurations:

a) **settings.py:** this contains the standard deployment settings. This does not contain any sensitive information - any items that use sensitive information are sourced from `.env` file using Python `os.getenv("VAR_NAME")`.


b) **test_settings.py:** this contains the settings required to run `PyTest` locally and on the Travis CI.


## Technologies Used

- [HTML](https://www.w3schools.com/html/default.asp)
  - This is the most fundamental component of a web page, providing the structure and content which can then be then be styled by CSS and interacted with by JavaScript.

- [CSS](https://www.w3schools.com/css/default.asp)
  - This is a styling language which is used to modify how the HTML is render to the user, for example, the fonts used, colours, sizes, etc.
  - To override default Bootstrap styling and provide my own custom styling I have created my own CSS file, base.css, which is applied to every page.

- [JavaScript](https://www.w3schools.com/Js/)
  - This language enables an interactive element to be added to websites, permitting realtime responsive pages.
  - The navigation menu becomes fixed once the user scrolls past the header and brand container, this is achieved using custom JS code and Bootstrap classes.

- [Python](https://www.python.org/)
  - This is the server side language the application has been developed using.

- [PostgreSQL](https://www.postgresql.org/)
  - This is an open source database which I have developed the application on.
  - I have created a docker container which runs PostgreSQL and interacts with the Python application.

- [Docker](https://www.docker.com/)
  - This is a technology which packages up applications into containers and runs them in an isolated container within a chosen operating system, which is seperate from the host operating system.

- [Zigbee2MQTT](https://www.zigbee2mqtt.io/)
  - This is installed on the Raspberry Pi and handles all the communications received by the Zigbee sniffer.

- [Mosquitto](https://mosquitto.org/)
  - An MQTT broker which is where all Zigbee device communications are published.
  - Smart Hub connects to this server to listen for communications.

### Frameworks

- [Bootstrap](https://getbootstrap.com/)
  - This is a front-end framework which is built using HTML and CSS. It makes it easy to create responsive websites using a grid system with screen-width breakpoints.

- [JQuery](https://jqueryui.com/)
  - This is a JavaScript framework which enables easy manipulation of the Document Object Model (DOM) using JQuery syntax.
  - This was used to provide the interactive functionality for fetching device's and device command's for setting up event triggers and responses.

- [Font Awesome](https://fontawesome.com/)
  - This is a font library which I have used to provide some context appropriate icons throughout the application. These are visible throughout, from menu icons to headers.

- [Django](https://www.djangoproject.com/)
  - This is a high-level python framework which provides advanced functionality with minimal effort from the developer.
  - The application is developed using Django and extensively uses built-in functionality and custom packages.

- [Django-allauth](https://www.intenct.nl/projects/django-allauth/)
  - This package is an add-on for Django which implements a third-party authentication system. It provides advanced functionality, such as the integration of external social authentication, e.g. allowing users to authenticate with your website using their Google account, in addition to local authentication.
  - For this application I have used this package for its additional security, as it will only permit a user to attempt to login with incorrect details 5 times before restricting their ability to do so. 
  - The ability to log-in via Google OAuth is provided by this package.

- [Django-crispy-forms](https://github.com/django-crispy-forms/django-crispy-forms)
  - This package renders Django forms using Bootstrap conventions and classes, effectively making the forms responsive and mobile-first.
  - It permits customised form rendering in a much more programmatic fashion compared to Django's default implementation.

## Testing

### Automated

Each app within the platform has a `tests/` folder which contains relevant testings for that specific app. For **coverage report** of overall testing, click the `CodeCov badge` at the top of the readme.

To run testing locally, use the following command:
  `docker-compose run --rm web python -m pytest .`

### Manual

In addition to the automated testing, I conducted some manual testing across a number of browsers and devices. This was to ensure, the pages rendered as expected, and that screen space was optimally utilised.

| # | Test | Test Criteria | Result |
|---|------|--------|------|
| 1 | Website is displayed correctly on multiple browsers | Tested on Chrome, Safari, and Edge | Passed |
| 2 | Website is responsive and displayed correctly on multiple devices | Tested on Macbook Pro, Windows Laptop, OnePlus 7T, and iPhone | Passed |
| 3 | Forms do not permit entry of invalid data; invalid entries receive an error message | Attempting to edit HTML form inputs to create fields that don't exist - should return invalid | Passed |
| 4 | All links work | Check that all links are work | Passed |
| 5 | Images, icons, and buttons render correctly | Visual inspection of every page | Passed |

### Known bugs

There are no known bugs at present.
## Deployment

### ENV file

| KEY  | VALUE | DESCRIPTION |
| ---- | ----- | ----------- |
| `DJANGO_SECRET_KEY` | `use-a-secret-phrase` | It is important to use a secure hash here |
| `POSTGRES_DB` | `smarthub` | Use the value from your PostgreSQL database |
| `POSTGRES_USER` | `smarthub` | Use the value from your PostgreSQL database |
| `POSTGRES_PASSWORD` | `smarthub` | Use the value from your PostgreSQL database |
| `EMAIL_HOST` | `smtp.gmail.com` | This is used for sending email notifications and registration emails.
| `EMAIL_HOST_USER` | `dummy-email-address@gmail.com` | This will be the account used to send email notifications |
| `EMAIL_HOST_PASSWORD` | `app-key` |
| `MQTT_QOS` | `1` | The Quality of Service level you want to guarantee - see [here](https://mosquitto.org/man/mqtt-7.html)
| `MQTT_SERVER` | `192.168.x.x` | The IP address of the server running the MQTT broker (mentioned in [Zigbee Communication Sniffing](#zigbee-communication-sniffing)) - usually a LAN address |
| `MQTT_BASE_TOPIC` | `zigbee2mqtt` |
| `MQTT_CLIENT_NAME` | `Smart Hub` |
| `ARCH_IMAGE` | `postgres` | Only set this value if you are using a CPU architecture other than ARM64 (e.g. not a Raspberry Pi)
| `SOCIAL_GOOGLE_CLIENT_ID` | `` | Follow the sets in [here](https://django-allauth.readthedocs.io/en/latest/providers.html#google) to obtain this value
| `SOCIAL_GOOGLE_SECRET` | `` | Follow the sets in [here](https://django-allauth.readthedocs.io/en/latest/providers.html#google) to obtain this value

### Zigbee Communication Sniffing

As I was developing an end-to-end solution, I needed a way for _sniff_ communications from the zigbee devices. I opted not use to a Zigbee router as this would require investment in a brand and likely would come with limitations placed by the manufacturer. Instead, I opted to purchase this [Zigbee sniffer](https://www.amazon.co.uk/dp/B07YDG4QHM/ref=cm_sw_r_cp_apa_glt_fabc_KVCAQ6ETZ1WWWKGCQJY0?_encoding=UTF8&psc=1&pldnSite=1).

To setup the hardware device, it needs to be flashed with custom firmware that publishes to an MQTT broker - see [instructions here](https://www.zigbee2mqtt.io/information/alternative_flashing_methods.html).

For this to work, you must have an MQTT broker installed - in this case I opted to use [Mosquitto](https://mosquitto.org/) with default settings.

With all of the above in place, we can move on to deployment of the platform.

### Raspberry Pi with Raspbian 

1. Setup hardware for sniffing Zigbee communications - see [Zigbee Communication Sniffing](#zigbee-communication-sniffing)

2. Setup [Zigbee2MQTT](https://www.zigbee2mqtt.io/getting_started/running_zigbee2mqtt.html)

3. Configure `.env` to point to `MQTT_SERVER`

4. Install `Docker `by following the steps listed on [Docker](https://docs.docker.com/engine/install/debian/#install-using-the-convenience-script)

5. [Install Git](https://projects.raspberrypi.org/en/projects/getting-started-with-git/3)

6. Continue with the steps at [Starting the application](#starting-the-application)

### Local machine deployment

1. If you are running any CPU arch other than `ARM64` you will need to ensure that the following is added to your `.env` file - by default the `Dockerfile` is configured to download an `ARM64` compatiable image - addingt this ENV variable will ensure it runs on all other architectures.
    - `ARCH_IMAGE="postgres"`

2. Download and install `Docker` and `docker-compose` by following the steps on [Docker](https://docs.docker.com/get-docker/)

3. [Install Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

4. Continue with the steps at [Starting the application](#starting-the-application)

### Starting the application

1. Clone the Git repo using:
    - `git clone https://github.com/jyoung90ie/qub-dissertation.git`

2. Open the cloned folder in the shell (`cd folder-name`)

3. Build the Docker containers
    - `docker-compose build`

4. Apply the database migrations
    - `docker-compose run --rm web python -m manage migrate`

5. Create a `superuser` account (for accessing admin areas) - follow the shell prompt
    - `docker-compose run --rm web python -m manage createsuperuser`
    
6. Start up the docker containers in `detached mode` (in the background)
    - `docker-compose up -d`

7. To check the logs, for example, for the `web` container - for others replace `web` with the container name:
    - `docker-compose logs -f web`

8. Navigate to the Smart Hub interface, replacing `ip-address` with the IP of the Raspberry Pi device
    - `http://ip-address:8080`

9. Access admin area using the `superuser` account created in `Step 10`
    - `http://ip-address:8080/admin`

## Notification setup
### Pushbullet

If you wish to receive notifications on your mobile devices and/or computer, Smart Hub integrates with [Pushbullet](https://www.pushbullet.com/). 

In order for notifications to work, you will need to setup an account at Pushbullet, then create an `Access Token` [here](https://www.pushbullet.com/#settings/account).

Copy the `Access Token`, open the Smart Hub web page and follow the steps below:

1. Login to your account

2. Navigate to `Events` -> `Notifications`

3. Click the green [ + ] button at the top to create a new `Notification Channel`

4. Select `Pushbullet` from the dropdown

5. Ensure `Enable notifications` is checked

6. Paste in the `Access Token` in the `API token` input box

7. Click `Save`

8. Download the `Pushbullet` app on your desktop or mobile device and `login`

9. Pushbullet notifications are now setup and will be pushed to all devices you have the app installed

You will only receive notifications when you have created an `Event` with at least one `Event Trigger` in Smart Hub - notifications must be enabled.

### Email

If you wish to receive email notifications when Smart Hub `Events` are `triggered`, you will need to add SMTP email server settings to the `.env` file as detailed under the heading [ENV file](#env-file). _**NOTE**: an SMTP server must be configured before email notifications will work._

Click [here](#generating-gmail-app-password) to see the steps for clicking a Gmail app password.

1. Go back to `Smart Hub` and login to your account

2. Navigate to `Events` -> `Notifications`

3. Click the green [ + ] button at the top to create a new `Notification Channel`

4. Select `Email` from the dropdown

5. Input a valid email address for `From Email` - this details who the email will come from - **note**: this is will only work if you use your own SMTP, i.e. for Gmail the from address will show as the `EMAIL_HOST_USER` in the `.env` file.

6. Input a valid email address for `To Email` - this is where the emails notifications will be sent.

7. Click `Save`

9. Email notifications are now setup. 

You will only receive notifications when you have created an `Event` with at least one `Event Trigger` in Smart Hub - notifications must be enabled

#### Generating Gmail App Password

1. Login to your Gmail account

2. Go to `Manage your Google Account` by clicking the button on the top right of your Gmail screen

3. Go to `Security`

4. Select `App passwords` under the heading `Signing in to Google`

5. For `Select app` -> `Other (custom name)` -> input `Smart Hub`

6. Click `Generate` and copy the `app password` generated

7. Paste the `app password` into the file `.env`
    - `EMAIL_HOST_PASSWORD="app-password-here"`


### Acknowledgements

- Dissertation Supervisor
  - **Neil Anderson** provided guidance and feedback at various points throughout the development process.