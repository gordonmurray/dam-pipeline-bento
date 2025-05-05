<script lang="ts">
	import { onMount } from 'svelte';

	let images = [];

	onMount(async () => {
		const res = await fetch('https://your-fastapi-endpoint/images');
		images = await res.json();
	});
</script>

<h1>Image Gallery</h1>

{#each images as image}
	<div style="margin-bottom: 1rem;">
		<img src={`https://your-r2-endpoint/${image.r2_key}`} alt={image.caption} width="200" />
		<p>{image.caption}</p>
		<small>{image.filename}</small>
	</div>
{/each}
