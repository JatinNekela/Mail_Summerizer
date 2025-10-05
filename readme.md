install docker desktop  
pull the repo   

before doing docker compose up --build  
create .env file 
    GMAIL_USER = "your email (inside quotes)"  
    GMAIL_APP_PASSWORD = "have to generate this password for third party use from google account -> security -> app passwords (insed quotes)"  
    CEREBRAS_API_KEY="your cerebras api key (inside quotes)"  (default)  

now do docker compose up --build -d wait for mail-connector container to run
then open http://localhost:5000/ for ui  
select model (choose llama3.1-8b)  
click fetch & sumarize mail