<script lang="ts">
  let file: File | null = null;
  let caption = '';

  async function upload() {
    if (!file) return alert("Choose a file");

    const form = new FormData();
    form.append('file', file);
    form.append('caption', caption);

    const res = await fetch('https://dam-producer.fly.dev/upload', {
      method: 'POST',
      body: form
    });

    if (res.ok) {
      alert("Uploaded!");
    } else {
      alert("Error uploading");
    }
  }
</script>

<h1>Upload Image</h1>
<input type="file" on:change={(e) => file = e.target.files?.[0] ?? null} />
<input type="text" placeholder="Caption" bind:value={caption} />
<button on:click={upload}>Upload</button>
