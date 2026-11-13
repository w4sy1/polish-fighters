package io.github.openlf2.openlf2;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Bounded, allowlisted source discovery for the Android mod browser. */
final class AndroidModSources {
    static final class Source {
        final String name, host, page;
        Source(String name, String host, String page) { this.name=name; this.host=host; this.page=page; }
    }
    static final class Candidate {
        final String label, url;
        Candidate(String label, String url) { this.label=label; this.url=url; }
        @Override public String toString() { return label + "\n" + url; }
    }
    static final class RobotsRule {
        final boolean allow; final String path;
        RobotsRule(boolean allow,String path){this.allow=allow;this.path=path;}
    }
    static final List<Source> SOURCES = Collections.unmodifiableList(Arrays.asList(
        new Source("Little Fighter Empire — wersje", "www.lf-empire.de", "https://www.lf-empire.de/lfe-fileplanet/versions"),
        new Source("Little Fighter Empire — mody", "www.lf-empire.de", "https://www.lf-empire.de/lfe-fileplanet/mods"),
        new Source("ModDB — Little Fighter 2", "www.moddb.com", "https://www.moddb.com/games/little-fighter-21/mods"),
        new Source("LF Empire Forum", "lf-empire.de", "https://lf-empire.de/forum/"),
        new Source("Ultimate Fighters Forum", "theultimatefighters.forumotion.com", "https://theultimatefighters.forumotion.com/t26p25-lf2-mods-all")
    ));
    private static final int MAX_PAGE=2*1024*1024;
    private static final Pattern LINK=Pattern.compile("(?is)<a\\b[^>]*href\\s*=\\s*['\"]([^'\"]+)['\"][^>]*>(.*?)</a>");
    private static final Map<String,Long> LAST_REQUEST=new ConcurrentHashMap<>();
    private AndroidModSources() {}

    static List<Candidate> discover(Source source) throws IOException {
        if (!host(source.page).equals(source.host)) throw new IOException("Źródło nie pasuje do listy zaufanych domen.");
        checkRobots(source);
        return parsePage(source,fetch(source.page, source.host,0));
    }

    static List<Candidate> parsePage(Source source,String html) throws IOException {
        List<Candidate> result = new ArrayList<>();
        Matcher links=LINK.matcher(html);
        while (links.find() && result.size()<100) {
            String href=links.group(1).trim();
            String label=links.group(2).replaceAll("(?is)<[^>]+>", " ").replaceAll("\\s+", " ").trim();
            if (label.isEmpty() || label.length()>160) continue;
            URL target=new URL(new URL(source.page), href);
            if (!"https".equalsIgnoreCase(target.getProtocol()) || !target.getHost().equalsIgnoreCase(source.host)) continue;
            String path=target.getPath();
            boolean project=source.host.equals("www.moddb.com") && path.matches("/mods/[^/]+/?")
                || source.host.equals("www.lf-empire.de") && path.matches("/lfe-fileplanet/(versions|mods)/[0-9]+[^/]*")
                || source.host.equals("lf-empire.de") && path.endsWith("showthread.php");
            if (!project || path.equals("/mods/top") || path.equals("/mods/latest") || path.equals("/mods/add")) continue;
            String url=target.toExternalForm();
            boolean duplicate=false; for (Candidate item:result) if(item.url.equals(url)){duplicate=true;break;}
            if(!duplicate) result.add(new Candidate(label,url));
        }
        return result;
    }

    private static void checkRobots(Source source) throws IOException {
        String robots=readRobots(source.host);
        String path=new URL(source.page).getPath();
        double delay=5;
        boolean group=false, seenDirective=false;
        List<RobotsRule> rules=new ArrayList<>();
        for(String raw:robots.split("\\r?\\n")) {
            String line=raw.replaceAll("#.*$","").trim();int colon=line.indexOf(':');if(colon<0)continue;
            String key=line.substring(0,colon).trim().toLowerCase(Locale.ROOT),value=line.substring(colon+1).trim();
            if(key.equals("user-agent")) {
                if(seenDirective)group=false;
                group=group||value.equals("*")||value.toLowerCase(Locale.ROOT).contains("polishlittlefighters");
            } else if(group&&key.equals("allow")&&!value.isEmpty()) { rules.add(new RobotsRule(true,value));seenDirective=true; }
            else if(group&&key.equals("disallow")&&!value.isEmpty()) { rules.add(new RobotsRule(false,value));seenDirective=true; }
            else if(group&&key.equals("crawl-delay")) try { delay=Math.max(delay,Math.min(120,Double.parseDouble(value)));seenDirective=true; } catch(NumberFormatException ignored) {}
        }
        if(!robotsAllowed(path,rules))throw new IOException("robots.txt zabrania odczytu tej strony.");
        long now=System.nanoTime()/1_000_000L;
        Long last=LAST_REQUEST.get(source.host);
        if(last!=null&&now-last<delay*1000)throw new IOException("Źródło wymaga dłuższego odstępu; spróbuj później.");
        LAST_REQUEST.put(source.host,now);
    }

    static boolean robotsAllowed(String path,List<RobotsRule> rules) {
        RobotsRule best=null;int specificity=-1;
        for(RobotsRule rule:rules) {
            StringBuilder regex=new StringBuilder("^");int score=0;
            for(int i=0;i<rule.path.length();i++) {
                char c=rule.path.charAt(i);
                if(c=='*')regex.append(".*");
                else if(c=='$'&&i==rule.path.length()-1)regex.append('$');
                else {regex.append(Pattern.quote(String.valueOf(c)));score++;}
            }
            if(!rule.path.endsWith("$"))regex.append(".*");
            if(Pattern.compile(regex.toString()).matcher(path).matches()&&(score>specificity||(score==specificity&&rule.allow))) {
                best=rule;specificity=score;
            }
        }
        return best==null||best.allow;
    }

    private static String readRobots(String host) throws IOException {
        URL url=new URL("https://"+host+"/robots.txt");
        HttpURLConnection connection=(HttpURLConnection)url.openConnection();connection.setConnectTimeout(8000);connection.setReadTimeout(8000);
        connection.setInstanceFollowRedirects(false);connection.setRequestProperty("User-Agent","PolishLittleFighters-ModBrowser/1.0");
        try {
            int code=connection.getResponseCode();
            if(code==404)return "";
            if(code!=200)throw new IOException("Nie można sprawdzić robots.txt; źródło pominięto.");
            try(InputStream input=connection.getInputStream();ByteArrayOutputStream output=new ByteArrayOutputStream()) {
                byte[] buffer=new byte[4096];int n;
                while((n=input.read(buffer))!=-1){if(output.size()+n>MAX_PAGE)throw new IOException("robots.txt przekracza limit.");output.write(buffer,0,n);}
                return new String(output.toByteArray(),StandardCharsets.UTF_8);
            }
        } finally { connection.disconnect(); }
    }

    private static String fetch(String address, String allowedHost,int redirects) throws IOException {
        URL url=new URL(address);
        HttpURLConnection connection=(HttpURLConnection)url.openConnection();
        connection.setConnectTimeout(10000); connection.setReadTimeout(12000); connection.setInstanceFollowRedirects(false);
        connection.setRequestProperty("User-Agent","PolishLittleFighters-ModBrowser/1.0");
        int code=connection.getResponseCode();
        if(code>=300 && code<400) {
            String location=connection.getHeaderField("Location"); connection.disconnect();
            if(location==null) throw new IOException("Źródło zwróciło niepełne przekierowanie.");
            if(redirects>=3)throw new IOException("Za dużo przekierowań źródła.");
            URL redirected=new URL(url,location);
            if(!"https".equalsIgnoreCase(redirected.getProtocol()) || !redirected.getHost().equalsIgnoreCase(allowedHost))
                throw new IOException("Przekierowanie poza zweryfikowaną domenę zostało zablokowane.");
            return fetch(redirected.toExternalForm(),allowedHost,redirects+1);
        }
        if(code!=200) { connection.disconnect(); throw new IOException("Źródło odpowiedziało kodem HTTP "+code+"."); }
        String type=connection.getContentType();
        if(type==null || !type.toLowerCase(Locale.ROOT).contains("text/html")) { connection.disconnect(); throw new IOException("Źródło nie zwróciło strony HTML."); }
        try(InputStream input=connection.getInputStream();ByteArrayOutputStream output=new ByteArrayOutputStream()) {
            byte[] buffer=new byte[8192]; int n;
            while((n=input.read(buffer))!=-1) { if(output.size()+n>MAX_PAGE) throw new IOException("Strona źródłowa przekracza limit 2 MiB."); output.write(buffer,0,n); }
            return new String(output.toByteArray(),StandardCharsets.UTF_8);
        } finally { connection.disconnect(); }
    }
    private static String host(String address) throws IOException { return new URL(address).getHost().toLowerCase(Locale.ROOT); }
}
