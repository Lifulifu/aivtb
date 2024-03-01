<script lang="ts">
  import { onDestroy, onMount } from "svelte";

  const subtitleUrl = 'ws://localhost:8000/subtitle';
  let question: string = "";
  let subtitle: string = "";
  let subtitleWs: WebSocket;
  const testSubtitle = "測試測試測試測試測試測試測試\n測試測試測試測試測試測試測試測試測試"

  let questionTimer: number;
  let subtitleTimer: number;
  const SUBTITLE_TTL = 15000;
  const QUESTION_TTL = 20000;
  const SUBTITLE_DELAY = 5000;

  onMount(async () => {
    await connectSubtitle();
  })

  onDestroy(() => {
    subtitleWs.close();
  })

  function typeQuestion(text: string) {
    let i = 0;
    question = '';
    function _typeQuestion() {
      if (i < text.length) {
        question = question + text.charAt(i);
        i++;
        setTimeout(_typeQuestion, 50);
      }
    }
    _typeQuestion();
  }

  async function connectSubtitle() {
    if (subtitleWs) subtitleWs.close();
    subtitleWs = new WebSocket(subtitleUrl);
    subtitleWs.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if(data && data.status === 'start') {
          if (data.role === 'user') {
            typeQuestion(data.text);
            subtitle = '';
            clearTimeout(questionTimer);
            questionTimer = setTimeout(() => {
              question = '';
            }, QUESTION_TTL);
          }
          else {
            setTimeout(() => {
              subtitle = data.text;
              clearTimeout(subtitleTimer);
              subtitleTimer = setTimeout(() => {
                subtitle = '';
              }, SUBTITLE_TTL);
            }, SUBTITLE_DELAY)
          }
        }
      } catch (e) {
        console.log(e)
      }

    }
    subtitleWs.onerror = (e) => {
      console.error(e)
    }
  }

  function onPopulateClick() {
    question = testSubtitle;
    subtitle = testSubtitle;
  }

  function onClearClick() {
    question = '';
    subtitle = '';
  }
</script>

<div class="flex p-4 gap-2 items-center">
  <button
  class="bg-gray-300 py-2 px-4 rounded-md"
  on:click={onPopulateClick}>
    Populate
  </button>

  <button
  class="bg-gray-300 py-2 px-4 rounded-md"
  on:click={onClearClick}>
    Clear
  </button>
</div>

<div class="w-full text-center absolute bottom-8 left-1/2 -translate-x-1/2">
  {#if question !== ''}
    <div class="ml-8 flex gap-2 items-center">
      <img class="inline-block w-20" src="/src/assets/user.png"/>
      <div class="w-[50%] text-black bg-white rounded-md border border-gray-400 p-4 text-2xl font-bold">
        {question}
      </div>
    </div>
  {/if}
  <p class="subtitle assistant mt-4"> {subtitle} </p>
</div>

<style>
  :global(body) {
    width: 100%;
    height: 100svh;
    position: relative;
    background-color: #00FF00;
  }

  .subtitle {
    --text-border-color: #000000;
    --text-border-width: 2px;

    font-size: 3rem;
    font-weight: 800;
    padding: 0;
    font-family: 標楷體;

    text-shadow:
      var(--text-border-width) var(--text-border-width) 0 #000,
      calc(-1 * var(--text-border-width)) var(--text-border-width) 0 #000,
      calc(-1 * var(--text-border-width)) calc(-1 * var(--text-border-width)) 0 #000,
      var(--text-border-width) calc(-1 * var(--text-border-width)) 0 #000;
  }

  .subtitle.assistant {
    color: rgb(243, 221, 109);
  }
</style>