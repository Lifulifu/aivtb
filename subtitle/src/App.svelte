<script lang="ts">
  import { onMount } from "svelte";

  const url = 'ws://localhost:8000/stream_finished_tts';
  let text = ''

  onMount(() => {
    const ws = new WebSocket(url)
    ws.onmessage = (e) => {
      console.log(e.data)
      text = e.data.a;
    }
  })
</script>

<div class="bg-gray-200 font-bold">{text}</div>
