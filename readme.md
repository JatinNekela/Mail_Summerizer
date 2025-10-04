install docker desktop
pull the repo 
before doing docker compose up --build
create .env file 
    GMAIL_USER = "your email (inside quotes)"
    GMAIL_APP_PASSWORD = "have to generate this password for third party use from google account -> security -> app passwords"
    OLLAMA_API_URL="http://ollama:11434/api/generate"  (default)
if you have <= 8GB RAM go to setup_ollama.sh remove these teo lines echo "Pulling llama3 model..." 
                                                                            ollama pull llama3
only download gemma 
now do docker compose up --build wait for images and models to install
then open http://localhost:5000/ for ui and check http://localhost:11434/  it will show "Ollama is running ".