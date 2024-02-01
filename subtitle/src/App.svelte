<script lang="ts">
  import { onMount } from "svelte";

  const subtitleUrl = 'ws://localhost:8000/subtitle';
  let subtitle: string[] = [];
  let subtitleWs: WebSocket;
  const testSubtitle = "測試測試測試測試測試測試測試\n測試測試測試測試測試測試測試測試測試"

  let timer: number;
  const SUBTITLE_TTL = 10000;
  const SUBTITLE_DELAY = 4000;

  onMount(async () => {
    await connectSubtitle();
  })

  async function connectSubtitle() {
    if (subtitleWs) subtitleWs.close();
    subtitleWs = new WebSocket(subtitleUrl);
    subtitleWs.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if(data) {
          console.log(data)
          setTimeout(() => {
            subtitle = data;
            clearTimeout(timer);
            timer = setTimeout(() => (subtitle = []), SUBTITLE_TTL);
          }, SUBTITLE_DELAY)
        }
      } catch (e) {
        console.log(e)
      }

    }
    subtitleWs.onerror = (e) => {
      console.error(e)
    }
  }
</script>

<div class="flex p-4 gap-2 items-center">
  <button class="bg-gray-300 py-2 px-4 rounded-md" on:click={() => subtitle = [testSubtitle]}>Populate</button>
  <button class="bg-gray-300 py-2 px-4 rounded-md" on:click={() => subtitle = []}>Clear</button>
</div>

<div class="subtitle w-full text-center absolute bottom-8 left-1/2 -translate-x-1/2">
  {subtitle}
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

    color: rgb(243, 221, 109);
    font-size: 4rem;
    font-weight: 800;
    padding: 0 10% 0;
    font-family: 標楷體;

    text-shadow:
      var(--text-border-width) var(--text-border-width) 0 #000,
      calc(-1 * var(--text-border-width)) var(--text-border-width) 0 #000,
      calc(-1 * var(--text-border-width)) calc(-1 * var(--text-border-width)) 0 #000,
      var(--text-border-width) calc(-1 * var(--text-border-width)) 0 #000;
  }
</style>