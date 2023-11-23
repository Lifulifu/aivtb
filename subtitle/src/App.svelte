<script lang="ts">
  import { onMount } from "svelte";

  const subtitleUrl = 'ws://localhost:8000/stream_subtitle';
  let subtitle: string[] = [];
  let subtitleWs: WebSocket;

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
          subtitle = data;
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

    color: rgb(236, 247, 141);
    font-size: 4rem;
    font-weight: 800;
    padding: 0 10% 0;

    text-shadow:
      var(--text-border-width) var(--text-border-width) 0 #000,
      calc(-1 * var(--text-border-width)) var(--text-border-width) 0 #000,
      calc(-1 * var(--text-border-width)) calc(-1 * var(--text-border-width)) 0 #000,
      var(--text-border-width) calc(-1 * var(--text-border-width)) 0 #000;
  }
</style>