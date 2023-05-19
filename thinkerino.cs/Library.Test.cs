using System;
using Xunit;

namespace Thinkerino
{
    public class Library
    {
        [Fact]
        public void Test1()
        {
            var res = Say.hello("gigi");
            Assert.Equal("Hello gigi", res);
        }
    }
}