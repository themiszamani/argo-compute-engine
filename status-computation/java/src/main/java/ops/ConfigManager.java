package ops;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.util.HashMap;
import java.util.Map.Entry;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

public class ConfigManager {

	public String tenant;
	public String job;
	public String egroup; // endpoint group
	public String ggroup; // group of groups
	public HashMap<String, String> egroupTags;
	public HashMap<String, String> ggroupTags;
	public HashMap<String, HashMap<String, String>> datastore_map;

	public ConfigManager() {
		this.tenant = null;
		this.job = null;
		this.egroup = null;
		this.ggroup = null;
		this.egroupTags = new HashMap<String, String>();
		this.ggroupTags = new HashMap<String, String>();
		this.datastore_map = new HashMap<String, HashMap<String, String>>();
	}

	public void clear() {
		this.tenant = null;
		this.job = null;
		this.egroup = null;
		this.ggroup = null;
		this.egroupTags.clear();
		this.ggroupTags.clear();
		this.datastore_map.clear();
	}

	public void loadJson(File json_file) throws FileNotFoundException {
		// Clear data
		this.clear();

		BufferedReader br = new BufferedReader(new FileReader(json_file));
		JsonParser jsonParser = new JsonParser();
		JsonElement jElement = jsonParser.parse(br);
		JsonObject jObj = jElement.getAsJsonObject();

		// Get the simple fields
		this.tenant = jObj.getAsJsonPrimitive("tenant").getAsString();
		this.job = jObj.getAsJsonPrimitive("job").getAsString();
		this.egroup = jObj.getAsJsonPrimitive("egroup").getAsString();
		this.ggroup = jObj.getAsJsonPrimitive("ggroup").getAsString();

		// Get compound fields
		JsonObject jEgroupTags = jObj.getAsJsonObject("egroup_tags");
		JsonObject jGgroupTags = jObj.getAsJsonObject("ggroup_tags");
		JsonObject jDataMap = jObj.getAsJsonObject("datastore_maps");
		
		// Get compound fields
		for (Entry<String,JsonElement> item : jEgroupTags.entrySet()) {
			
			this.egroupTags.put(item.getKey(),item.getValue().getAsString());
		}
		for (Entry<String,JsonElement> item : jGgroupTags.entrySet()) {
			
			this.ggroupTags.put(item.getKey(),item.getValue().getAsString());
		}
		
		// Get super compound field
		for (Entry<String,JsonElement> item : jDataMap.entrySet()) {
			String itemKey = item.getKey();
			this.datastore_map.put(itemKey,new HashMap<String,String>());
			
			JsonObject jSubObj = item.getValue().getAsJsonObject();
			for (Entry<String,JsonElement> subitem : jSubObj.entrySet())
			{
				this.datastore_map.get(itemKey).put(subitem.getKey(), subitem.getValue().getAsString());
			}
		}
		
		

	}

}
