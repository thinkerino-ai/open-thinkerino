using static Thinkerino.Logic.Language;
namespace Thinkerino.CSharp
{
    public class Wrapper
    {
        public static string Foo() {
            return new Language().LanguageId.ToString();
        }
    }
}
